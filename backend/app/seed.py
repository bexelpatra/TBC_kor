"""시드 — 최초 관리자(master) 생성. `python -m app.seed` 로 실행.

비밀번호는 코드에 두지 않고 환경변수 MASTER_ADMIN_PASSWORD로 주입한다.
"""
import os

from sqlalchemy import select

from app.database import SessionLocal
from app.models import Admin
from app.security import hash_password


def seed_master():
    password = os.environ.get("MASTER_ADMIN_PASSWORD")
    if not password:
        raise SystemExit("MASTER_ADMIN_PASSWORD 환경변수를 설정한 뒤 다시 실행하세요.")

    db = SessionLocal()
    try:
        exists = db.execute(select(Admin).where(Admin.login_id == "master")).scalar_one_or_none()
        if exists:
            print("master 계정이 이미 존재합니다.")
            return
        db.add(Admin(
            login_id="master",
            password_hash=hash_password(password),
            name="마스터",
            role="관리자",
            level=10,
        ))
        db.commit()
        print("master 계정을 생성했습니다. 비밀번호는 MASTER_ADMIN_PASSWORD로 입력한 값입니다.")
    finally:
        db.close()


if __name__ == "__main__":
    seed_master()
