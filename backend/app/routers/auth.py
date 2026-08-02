"""인증 — user/admin 로그인, 내 정보, 비밀번호 변경."""
import re
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import schemas
from app.config import settings
from app.database import get_db
from app.deps import get_token_payload
from app.errors import bad_request, unauthorized
from app.models import Admin, AppUser
from app.security import (
    create_access_token,
    decrypt_name,
    hash_password,
    initial_user_password,
    name_hmac,
    verify_password,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login/user", response_model=schemas.UserTokenOut)
def login_user(body: schemas.UserLogin, db: Session = Depends(get_db)):
    user = db.execute(
        select(AppUser).where(
            AppUser.phone_tail == body.phone_tail,
            AppUser.name_hash == name_hmac(body.name),
            AppUser.deleted_at.is_(None),
        )
    ).scalar_one_or_none()
    if not user or not verify_password(body.password, user.password_hash):
        raise unauthorized("로그인 정보가 일치하지 않습니다")
    minutes = settings.jwt_user_minutes
    token, exp = create_access_token(user.id, "user", minutes)
    return schemas.UserTokenOut(
        access_token=token, expires_in=minutes * 60, expires_at=exp, must_change_pw=user.must_change_pw
    )


@router.post("/login/admin", response_model=schemas.AdminTokenOut)
def login_admin(body: schemas.AdminLogin, db: Session = Depends(get_db)):
    admin = db.execute(
        select(Admin).where(Admin.login_id == body.login_id, Admin.deleted_at.is_(None))
    ).scalar_one_or_none()
    if not admin or not verify_password(body.password, admin.password_hash):
        raise unauthorized("로그인 정보가 일치하지 않습니다")
    minutes = settings.jwt_admin_minutes
    token, exp = create_access_token(admin.id, "admin", minutes, {"role": admin.role, "level": admin.level})
    return schemas.AdminTokenOut(
        access_token=token, expires_in=minutes * 60, expires_at=exp, role=admin.role, level=admin.level
    )


@router.get("/me", response_model=schemas.MeOut)
def me(payload: dict = Depends(get_token_payload), db: Session = Depends(get_db)):
    actor, pid = payload["actor"], int(payload["sub"])
    exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
    if actor == "user":
        u = db.get(AppUser, pid)
        if not u:
            raise unauthorized()
        return schemas.MeOut(actor="user", id=pid, display_name=decrypt_name(u.name_enc), expires_at=exp)
    a = db.get(Admin, pid)
    if not a:
        raise unauthorized()
    return schemas.MeOut(actor="admin", id=pid, display_name=a.name, expires_at=exp)


@router.post("/password")
def change_password(body: schemas.PasswordChange, payload: dict = Depends(get_token_payload), db: Session = Depends(get_db)):
    actor, pid = payload["actor"], int(payload["sub"])
    if actor == "user":
        u = db.get(AppUser, pid)
        if not u or not verify_password(body.current, u.password_hash):
            raise unauthorized("현재 비밀번호가 일치하지 않습니다")
        if not re.fullmatch(r"\d{6}", body.new):
            raise bad_request("WEAK_PASSWORD", "비밀번호는 6자리 숫자")
        u.password_hash = hash_password(body.new)
        u.must_change_pw = False
    else:
        a = db.get(Admin, pid)
        if not a or not verify_password(body.current, a.password_hash):
            raise unauthorized("현재 비밀번호가 일치하지 않습니다")
        if len(body.new) < 8 or not re.search(r"[A-Za-z]", body.new) or not re.search(r"\d", body.new):
            raise bad_request("WEAK_PASSWORD", "비밀번호는 영문·숫자 혼합 8자 이상")
        a.password_hash = hash_password(body.new)
    db.commit()
    return {"ok": True}


# initial_user_password 는 사용자 등록 라우터에서 사용
__all__ = ["router", "initial_user_password"]
