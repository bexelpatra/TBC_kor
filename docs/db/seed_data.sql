-- seed_data.sql — 초기 시드 데이터
-- 입력 계약: ADR-011 (최초 관리자)
--
-- ⚠️ 비밀번호는 이 파일에 절대 기록하지 않는다.
--    최초 관리자 생성은 `python -m app.seed` 를 사용하고,
--    비밀번호는 환경변수 MASTER_ADMIN_PASSWORD 로 주입한다.
--
--      MASTER_ADMIN_PASSWORD='<생성한 강력한 비밀번호>' python -m app.seed
--
--    아래 INSERT 는 참고용 형태이며, password_hash 자리에는
--    반드시 bcrypt 해시가 들어가야 한다(평문 금지).
--
-- 최초 관리자 (master)
INSERT INTO admin (login_id, password_hash, name, role, level)
VALUES ('master', '<BCRYPT_HASH>', '마스터', '관리자', 10);

-- 부트스트랩 후 master 비밀번호 교체 권장.
