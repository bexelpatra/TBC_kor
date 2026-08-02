"""rename app_user.birth_ym -> student_number, drop YYMM 제약

Revision ID: 0002_student_number
Revises: 0001_init
Create Date: 2026-06-15

docs/db/migrations/V002__app_user_student_number.sql 과 동일한 DDL.
"""
from alembic import op

revision = "0002_student_number"
down_revision = "0001_init"
branch_labels = None
depends_on = None

DDL = r"""
ALTER TABLE app_user RENAME COLUMN birth_ym TO student_number;
ALTER TABLE app_user DROP CONSTRAINT app_user_birth_ym_check;
ALTER TABLE app_user ADD CONSTRAINT app_user_student_number_check CHECK (student_number ~ '^[0-9]{4}$');
"""

DOWN_DDL = r"""
ALTER TABLE app_user DROP CONSTRAINT app_user_student_number_check;
ALTER TABLE app_user RENAME COLUMN student_number TO birth_ym;
ALTER TABLE app_user ADD CONSTRAINT app_user_birth_ym_check CHECK (birth_ym ~ '^[0-9]{2}(0[1-9]|1[0-2])$');
"""


def upgrade():
    op.get_bind().exec_driver_sql(DDL)


def downgrade():
    op.get_bind().exec_driver_sql(DOWN_DDL)
