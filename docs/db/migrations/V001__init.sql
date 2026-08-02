-- V001__init.sql — 초기 스키마 (PostgreSQL 14+)
-- 입력 계약: /docs/architect/db_contract.md, schema.md
-- 적용: Backend Alembic이 본 DDL을 초기 리비전으로 래핑

-- ============================================================
-- 공통: updated_at 자동 갱신 트리거 함수
-- ============================================================
CREATE OR REPLACE FUNCTION set_updated_at() RETURNS trigger AS $$
BEGIN
    NEW.updated_at := now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- app_user (학부모-자녀 계정) — "user"는 예약어라 app_user 사용
-- ============================================================
CREATE TABLE app_user (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    phone_tail      CHAR(4)     NOT NULL CHECK (phone_tail ~ '^[0-9]{4}$'),
    name_enc        BYTEA       NOT NULL,
    name_hash       CHAR(64)    NOT NULL,
    birth_ym        CHAR(4)     NOT NULL CHECK (birth_ym ~ '^[0-9]{2}(0[1-9]|1[0-2])$'),
    password_hash   TEXT        NOT NULL,
    must_change_pw  BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at      TIMESTAMPTZ
);
CREATE UNIQUE INDEX uq_app_user_login ON app_user (phone_tail, name_hash) WHERE deleted_at IS NULL;
CREATE TRIGGER trg_app_user_updated BEFORE UPDATE ON app_user
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ============================================================
-- admin_user (강사/보조자/관리자)
-- ============================================================
CREATE TABLE admin_user (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    login_id        VARCHAR(50) NOT NULL CHECK (login_id ~ '^[A-Za-z0-9]+$'),
    password_hash   TEXT        NOT NULL,
    name            VARCHAR(50) NOT NULL,
    role            VARCHAR(10) NOT NULL CHECK (role IN ('강사','보조자','관리자')),
    level           SMALLINT    NOT NULL DEFAULT 1 CHECK (level BETWEEN 1 AND 10),
    nickname        VARCHAR(50),
    api_key_hash    TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at      TIMESTAMPTZ
);
CREATE UNIQUE INDEX uq_admin_user_login_id ON admin_user (login_id) WHERE deleted_at IS NULL;
CREATE TRIGGER trg_admin_user_updated BEFORE UPDATE ON admin_user
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ============================================================
-- lecture (강의 마스터)
-- ============================================================
CREATE TABLE lecture (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    lecture_at  TIMESTAMPTZ NOT NULL,
    round_no    INT         NOT NULL,
    admin_id    BIGINT      NOT NULL REFERENCES admin_user(id),
    subject     VARCHAR(100),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at  TIMESTAMPTZ
);
CREATE UNIQUE INDEX uq_lecture_round ON lecture (round_no) WHERE deleted_at IS NULL;
CREATE INDEX ix_lecture_at ON lecture (lecture_at);
CREATE TRIGGER trg_lecture_updated BEFORE UPDATE ON lecture
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ============================================================
-- lecture_user (학생별 수강 기록 = 격리 단위)
-- ============================================================
CREATE TABLE lecture_user (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    lecture_id  BIGINT       NOT NULL REFERENCES lecture(id),
    user_id     BIGINT       NOT NULL REFERENCES app_user(id),
    title       VARCHAR(200) NOT NULL,
    content     TEXT,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ  NOT NULL DEFAULT now(),
    deleted_at  TIMESTAMPTZ
);
CREATE UNIQUE INDEX uq_lecture_user ON lecture_user (lecture_id, user_id) WHERE deleted_at IS NULL;
CREATE INDEX ix_lecture_user_user ON lecture_user (user_id) WHERE deleted_at IS NULL;
CREATE INDEX ix_lecture_user_title ON lecture_user (title);
CREATE TRIGGER trg_lecture_user_updated BEFORE UPDATE ON lecture_user
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ============================================================
-- attachment (첨부 이미지, 폴리모픽)
-- ============================================================
CREATE TABLE attachment (
    id            BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    target_type   VARCHAR(20) NOT NULL CHECK (target_type IN ('lecture_user','notice')),
    target_id     BIGINT      NOT NULL,
    file_path     TEXT        NOT NULL,
    display_order SMALLINT    NOT NULL DEFAULT 0,
    title         VARCHAR(100),
    note          VARCHAR(255),
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at    TIMESTAMPTZ
);
CREATE INDEX ix_attachment_target ON attachment (target_type, target_id) WHERE deleted_at IS NULL;
CREATE TRIGGER trg_attachment_updated BEFORE UPDATE ON attachment
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ============================================================
-- comment (특강 댓글/답글, 1단계)
-- ============================================================
CREATE TABLE comment (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    lecture_user_id BIGINT      NOT NULL REFERENCES lecture_user(id),
    author_type     VARCHAR(10) NOT NULL CHECK (author_type IN ('user','admin')),
    author_id       BIGINT      NOT NULL,
    content         TEXT        NOT NULL,
    parent_id       BIGINT      REFERENCES comment(id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at      TIMESTAMPTZ
);
CREATE INDEX ix_comment_lecture_user ON comment (lecture_user_id) WHERE deleted_at IS NULL;
CREATE INDEX ix_comment_parent ON comment (parent_id);
CREATE TRIGGER trg_comment_updated BEFORE UPDATE ON comment
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- 1단계 답글 강제: parent가 또 부모를 가지면 거부
CREATE OR REPLACE FUNCTION check_comment_depth() RETURNS trigger AS $$
BEGIN
    IF NEW.parent_id IS NOT NULL THEN
        IF (SELECT parent_id FROM comment WHERE id = NEW.parent_id) IS NOT NULL THEN
            RAISE EXCEPTION '답글은 1단계만 허용됩니다';
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
CREATE TRIGGER trg_comment_depth BEFORE INSERT OR UPDATE ON comment
    FOR EACH ROW EXECUTE FUNCTION check_comment_depth();

-- ============================================================
-- notice (공지)
-- ============================================================
CREATE TABLE notice (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    notice_at   TIMESTAMPTZ  NOT NULL,
    serial_no   INT          NOT NULL,
    admin_id    BIGINT       NOT NULL REFERENCES admin_user(id),
    title       VARCHAR(200) NOT NULL,
    content     TEXT,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ  NOT NULL DEFAULT now(),
    deleted_at  TIMESTAMPTZ
);
CREATE UNIQUE INDEX uq_notice_serial ON notice (serial_no) WHERE deleted_at IS NULL;
CREATE INDEX ix_notice_at ON notice (notice_at);
CREATE TRIGGER trg_notice_updated BEFORE UPDATE ON notice
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
