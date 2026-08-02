# 스키마 (schema.md)

> 작성: DB | 입력 계약: /docs/architect/db_contract.md | 대상: PostgreSQL 14+
> 마이그레이션: `migrations/V001__init.sql` (실제 적용은 Backend의 Alembic이 래핑)

## 계약 대비 결정/변경 사항
- **테이블명 `app_user`** : `user`는 PostgreSQL 예약어 → 학부모-자녀 계정 테이블은 `app_user`로 명명.
- **soft delete + 유니크 공존** : 모든 자연키 유니크는 **부분 유니크 인덱스 `WHERE deleted_at IS NULL`** 로 구현 → 탈퇴/삭제 후 동일 키 재등록 허용.
- **회차/일련번호 자동 채번** : `round_no`, `serial_no`는 시퀀스 대신 *앱 트랜잭션에서 `MAX+1`* 로 채번(계약 ADR-010, 삭제 시 번호 유지). 동시성은 테이블 단위 advisory lock으로 직렬화 → 본 문서 하단 참조.
- **updated_at 자동 갱신** : 공통 트리거 `set_updated_at()`.
- **1단계 답글 강제** : `comment.parent_id`가 가리키는 부모는 `parent_id IS NULL`이어야 함 → 트리거 `check_comment_depth()`로 보장.
- **폴리모픽 attachment** : `(target_type, target_id)`는 FK 없이 앱에서 무결성 관리.

## ERD (텍스트)
```
admin_user 1───N lecture 1───N lecture_user N───1 app_user
                                │ 1
                                ├──N attachment   (target_type='lecture_user')
                                └──N comment 1──N comment(답글, 1단계)
admin_user 1───N notice 1───N attachment (target_type='notice')
```

## 공통 컬럼 (모든 테이블)
| 컬럼 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| id | BIGINT IDENTITY | - | PK |
| created_at | TIMESTAMPTZ | now() | 생성(가입/작성) |
| updated_at | TIMESTAMPTZ | now() | 수정(트리거 자동) |
| deleted_at | TIMESTAMPTZ | NULL | soft delete |

---

## app_user (학부모-자녀 계정)
| 컬럼 | 타입 | Nullable | 기본값 | 설명 |
|---|---|---|---|---|
| phone_tail | CHAR(4) | NO | - | 휴대전화 뒷번호, CHECK `^[0-9]{4}$` |
| name_enc | BYTEA | NO | - | 자녀 이름 AES 암호문 |
| name_hash | CHAR(64) | NO | - | 이름 HMAC-SHA256 hex(조회·유니크) |
| student_number_enc | BYTEA | NO | - | 번호 4자리 AES-GCM 암호문(앱에서 `^[0-9]{4}$` 검증) |
| password_hash | TEXT | NO | - | bcrypt(초기 `00`+번호 4자리) |
| must_change_pw | BOOLEAN | NO | true | 최초 로그인 변경 강제 |

- 부분 유니크: `(phone_tail, name_hash) WHERE deleted_at IS NULL`

## admin_user (강사/보조자/관리자)
| 컬럼 | 타입 | Nullable | 기본값 | 설명 |
|---|---|---|---|---|
| login_id | VARCHAR(50) | NO | - | CHECK `^[A-Za-z0-9]+$` |
| password_hash | TEXT | NO | - | bcrypt(영문·숫자 8자+) |
| name | VARCHAR(50) | NO | - | 이름(평문) |
| role | VARCHAR(10) | NO | - | CHECK IN ('강사','보조자','관리자') |
| level | SMALLINT | NO | 1 | CHECK 1–10 (현재 미사용) |
| nickname | VARCHAR(50) | YES | - | 닉네임 |
| api_key_hash | TEXT | YES | - | MCP API 키 해시(읽기 전용) |

- 부분 유니크: `(login_id) WHERE deleted_at IS NULL`

## lecture (강의 마스터)
| 컬럼 | 타입 | Nullable | 설명 |
|---|---|---|---|
| lecture_at | TIMESTAMPTZ | NO | 일시 |
| round_no | INT | NO | 회차(자동 채번 MAX+1) |
| admin_id | BIGINT | NO | FK→admin_user.id, 담당 강사 |
| subject | VARCHAR(100) | YES | 주제(관리자용) |

- 부분 유니크: `(round_no) WHERE deleted_at IS NULL`

## lecture_user (학생별 수강 기록 = 격리 단위)
| 컬럼 | 타입 | Nullable | 설명 |
|---|---|---|---|
| lecture_id | BIGINT | NO | FK→lecture.id |
| user_id | BIGINT | NO | FK→app_user.id |
| title | VARCHAR(200) | NO | 제목 |
| content | TEXT | YES | 내용 |

- 부분 유니크: `(lecture_id, user_id) WHERE deleted_at IS NULL`
- **격리**: user 조회는 항상 `user_id = 본인`.

## attachment (첨부 이미지, 폴리모픽)
| 컬럼 | 타입 | Nullable | 기본값 | 설명 |
|---|---|---|---|---|
| target_type | VARCHAR(20) | NO | - | CHECK IN ('lecture_user','notice') |
| target_id | BIGINT | NO | - | 대상 행 id(FK 없음) |
| file_path | TEXT | NO | - | 저장 키/상대경로 |
| display_order | SMALLINT | NO | 0 | 정렬 |
| title | VARCHAR(100) | YES | - | 제목 |
| note | VARCHAR(255) | YES | - | 비고 |

## comment (특강 댓글/답글)
| 컬럼 | 타입 | Nullable | 설명 |
|---|---|---|---|
| lecture_user_id | BIGINT | NO | FK→lecture_user.id |
| author_type | VARCHAR(10) | NO | CHECK IN ('user','admin') |
| author_id | BIGINT | NO | 작성자 id |
| content | TEXT | NO | 내용 |
| parent_id | BIGINT | YES | FK→comment.id, 답글(1단계) |

- 트리거 `check_comment_depth()`: parent_id 지정 시 부모의 parent_id가 NULL이어야 함.

## notice (공지)
| 컬럼 | 타입 | Nullable | 설명 |
|---|---|---|---|
| notice_at | TIMESTAMPTZ | NO | 일시 |
| serial_no | INT | NO | 일련번호(자동 채번 MAX+1) |
| admin_id | BIGINT | NO | FK→admin_user.id |
| title | VARCHAR(200) | NO | 제목 |
| content | TEXT | YES | 내용 |

- 부분 유니크: `(serial_no) WHERE deleted_at IS NULL`

---

## 자동 채번 동시성 처리
`round_no`/`serial_no`는 다음 패턴으로 Backend가 트랜잭션 내 채번:
```sql
BEGIN;
SELECT pg_advisory_xact_lock(<table_key>);          -- 테이블별 고정 키로 직렬화
INSERT INTO lecture(..., round_no, ...)
VALUES (..., COALESCE((SELECT MAX(round_no) FROM lecture), 0) + 1, ...);
COMMIT;
```
- soft delete된 행의 번호도 MAX 계산에 포함(번호 재사용 안 함).
