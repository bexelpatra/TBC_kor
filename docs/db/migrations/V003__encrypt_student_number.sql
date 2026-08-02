-- app_user.student_number 암호화: CHAR(4) -> BYTEA(AES-GCM), 컬럼명 student_number_enc
-- 이름(name_enc)과 동일한 AES-GCM 비결정 암호화. BYTEA라 정규식 CHECK 제거(검증은 앱 계층).
-- 가입자 없음 전제 → 행 데이터 백필 없음(USING 절은 빈 테이블이라 미실행).
ALTER TABLE app_user DROP CONSTRAINT app_user_student_number_check;
ALTER TABLE app_user ALTER COLUMN student_number TYPE BYTEA USING convert_to(student_number::text, 'UTF8');
ALTER TABLE app_user RENAME COLUMN student_number TO student_number_enc;
