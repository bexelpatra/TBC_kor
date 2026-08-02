"""app_user.student_number 암호화: CHAR(4) -> BYTEA(AES-GCM), 컬럼명 student_number_enc

Revision ID: 0004_encrypt_student_number
Revises: 0003_refactor_fk_and_columns
Create Date: 2026-06-22

docs/db/migrations/V003__encrypt_student_number.sql 과 동일한 DDL.
- 번호 4자리를 이름과 동일한 AES-GCM 비결정 암호화로 저장.
- BYTEA에는 정규식 CHECK를 걸 수 없어 제약 제거(검증은 앱 계층 `^[0-9]{4}$`).
- 가입자 없음 전제 → 행 데이터 백필 없음. USING 절은 빈 테이블이라 실행되지 않음.
"""
from alembic import op

revision = "0004_encrypt_student_number"
down_revision = "0003_refactor_fk_and_columns"
branch_labels = None
depends_on = None

UPGRADE = r"""
ALTER TABLE app_user DROP CONSTRAINT app_user_student_number_check;
ALTER TABLE app_user ALTER COLUMN student_number TYPE BYTEA USING convert_to(student_number::text, 'UTF8');
ALTER TABLE app_user RENAME COLUMN student_number TO student_number_enc;
"""

DOWNGRADE = r"""
ALTER TABLE app_user RENAME COLUMN student_number_enc TO student_number;
ALTER TABLE app_user ALTER COLUMN student_number TYPE CHAR(4) USING convert_from(student_number, 'UTF8');
ALTER TABLE app_user ADD CONSTRAINT app_user_student_number_check CHECK (student_number ~ '^[0-9]{4}$');
"""


def upgrade():
    op.get_bind().exec_driver_sql(UPGRADE)


def downgrade():
    op.get_bind().exec_driver_sql(DOWNGRADE)
