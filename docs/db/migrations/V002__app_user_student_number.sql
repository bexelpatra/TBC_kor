-- app_user.birth_ym -> student_number 로 변경, YYMM 제약 제거(숫자 4자리만 검사)
ALTER TABLE app_user RENAME COLUMN birth_ym TO student_number;
ALTER TABLE app_user DROP CONSTRAINT app_user_birth_ym_check;
ALTER TABLE app_user ADD CONSTRAINT app_user_student_number_check CHECK (student_number ~ '^[0-9]{4}$');
