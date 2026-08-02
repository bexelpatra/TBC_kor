"""FK 제거, 컬럼 리네이밍, comment polymorphic 분리, attachment target_type 확장

Revision ID: 0003_refactor_fk_and_columns
Revises: 0002_student_number
Create Date: 2026-06-21

변경 요약:
- FK 전체 제거 (6개)
- lecture.admin_id → admin_user_id
- notice.admin_id → admin_user_id
- lecture_user.user_id → app_user_id
- comment: author_type/author_id → app_user_id(nullable) + admin_user_id(nullable)
- attachment: target_type CHECK에 'comment' 추가
- 불필요 인덱스 제거: ix_lecture_user_title, ix_comment_parent
"""
from alembic import op

revision = "0003_refactor_fk_and_columns"
down_revision = "0002_student_number"
branch_labels = None
depends_on = None

UPGRADE = r"""
-- 1) FK 제거
ALTER TABLE lecture DROP CONSTRAINT lecture_admin_id_fkey;
ALTER TABLE lecture_user DROP CONSTRAINT lecture_user_lecture_id_fkey;
ALTER TABLE lecture_user DROP CONSTRAINT lecture_user_user_id_fkey;
ALTER TABLE comment DROP CONSTRAINT comment_lecture_user_id_fkey;
ALTER TABLE comment DROP CONSTRAINT comment_parent_id_fkey;
ALTER TABLE notice DROP CONSTRAINT notice_admin_id_fkey;

-- 2) 컬럼 리네이밍
ALTER TABLE lecture RENAME COLUMN admin_id TO admin_user_id;
ALTER TABLE notice RENAME COLUMN admin_id TO admin_user_id;
ALTER TABLE lecture_user RENAME COLUMN user_id TO app_user_id;

-- 3) comment: polymorphic → 분리 컬럼
ALTER TABLE comment ADD COLUMN app_user_id BIGINT;
ALTER TABLE comment ADD COLUMN admin_user_id BIGINT;
UPDATE comment SET app_user_id = author_id WHERE author_type = 'user';
UPDATE comment SET admin_user_id = author_id WHERE author_type = 'admin';
ALTER TABLE comment DROP COLUMN author_type;
ALTER TABLE comment DROP COLUMN author_id;

-- 4) attachment: target_type CHECK 확장
ALTER TABLE attachment DROP CONSTRAINT attachment_target_type_check;
ALTER TABLE attachment ADD CONSTRAINT attachment_target_type_check
    CHECK (target_type IN ('lecture_user', 'notice', 'comment'));

-- 5) 불필요 인덱스 제거
DROP INDEX ix_lecture_user_title;
DROP INDEX ix_comment_parent;
"""

DOWNGRADE = r"""
-- 5) 인덱스 복원
CREATE INDEX ix_lecture_user_title ON lecture_user (title);
CREATE INDEX ix_comment_parent ON comment (parent_id);

-- 4) attachment CHECK 원복
ALTER TABLE attachment DROP CONSTRAINT attachment_target_type_check;
ALTER TABLE attachment ADD CONSTRAINT attachment_target_type_check
    CHECK (target_type IN ('lecture_user', 'notice'));

-- 3) comment: 분리 → polymorphic 원복
ALTER TABLE comment ADD COLUMN author_type VARCHAR(10);
ALTER TABLE comment ADD COLUMN author_id BIGINT;
UPDATE comment SET author_type = 'user', author_id = app_user_id WHERE app_user_id IS NOT NULL;
UPDATE comment SET author_type = 'admin', author_id = admin_user_id WHERE admin_user_id IS NOT NULL;
ALTER TABLE comment ALTER COLUMN author_type SET NOT NULL;
ALTER TABLE comment ALTER COLUMN author_id SET NOT NULL;
ALTER TABLE comment ADD CONSTRAINT comment_author_type_check CHECK (author_type IN ('user', 'admin'));
ALTER TABLE comment DROP COLUMN app_user_id;
ALTER TABLE comment DROP COLUMN admin_user_id;

-- 2) 컬럼명 원복
ALTER TABLE lecture_user RENAME COLUMN app_user_id TO user_id;
ALTER TABLE notice RENAME COLUMN admin_user_id TO admin_id;
ALTER TABLE lecture RENAME COLUMN admin_user_id TO admin_id;

-- 1) FK 복원
ALTER TABLE lecture ADD CONSTRAINT lecture_admin_id_fkey FOREIGN KEY (admin_id) REFERENCES admin_user(id);
ALTER TABLE lecture_user ADD CONSTRAINT lecture_user_lecture_id_fkey FOREIGN KEY (lecture_id) REFERENCES lecture(id);
ALTER TABLE lecture_user ADD CONSTRAINT lecture_user_user_id_fkey FOREIGN KEY (user_id) REFERENCES app_user(id);
ALTER TABLE comment ADD CONSTRAINT comment_lecture_user_id_fkey FOREIGN KEY (lecture_user_id) REFERENCES lecture_user(id);
ALTER TABLE comment ADD CONSTRAINT comment_parent_id_fkey FOREIGN KEY (parent_id) REFERENCES comment(id);
ALTER TABLE notice ADD CONSTRAINT notice_admin_id_fkey FOREIGN KEY (admin_id) REFERENCES admin_user(id);
"""


def upgrade():
    op.get_bind().exec_driver_sql(UPGRADE)


def downgrade():
    op.get_bind().exec_driver_sql(DOWNGRADE)
