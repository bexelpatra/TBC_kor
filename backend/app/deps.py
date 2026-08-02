"""인증/권한 의존성."""
from fastapi import Depends, Header
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.errors import forbidden, unauthorized
from app.models import Admin, AppUser
from app.security import decode_access_token, hash_api_key


def _decode(authorization: str | None) -> dict:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise unauthorized()
    token = authorization.split(" ", 1)[1]
    try:
        return decode_access_token(token)
    except Exception:
        raise unauthorized("토큰이 유효하지 않거나 만료되었습니다")


def get_token_payload(authorization: str | None = Header(default=None)) -> dict:
    """user/admin 공용 — 토큰 페이로드 반환(만료 시간 표시 등에 사용)."""
    return _decode(authorization)


def get_current_user(authorization: str | None = Header(default=None), db: Session = Depends(get_db)) -> AppUser:
    payload = _decode(authorization)
    if payload.get("actor") != "user":
        raise forbidden("학부모 전용 API 입니다")
    user = db.get(AppUser, int(payload["sub"]))
    if not user or user.deleted_at is not None:
        raise unauthorized()
    return user


def get_current_admin(authorization: str | None = Header(default=None), db: Session = Depends(get_db)) -> Admin:
    payload = _decode(authorization)
    if payload.get("actor") != "admin":
        raise forbidden("관리자 전용 API 입니다")
    admin = db.get(Admin, int(payload["sub"]))
    if not admin or admin.deleted_at is not None:
        raise unauthorized()
    return admin


def require_level(min_level: int):
    """level 기반 권한 검사 — 현재는 골격만(임계값 0, 전부 통과)."""
    threshold = 0  # TODO: 운영 시 min_level 적용

    def _checker(admin: Admin = Depends(get_current_admin)) -> Admin:
        if admin.level < threshold:
            raise forbidden(f"level {min_level} 이상 필요")
        return admin

    return _checker


def require_mcp_admin(x_api_key: str | None = Header(default=None), db: Session = Depends(get_db)) -> Admin:
    """MCP 전용 — 관리자 API 키 인증(읽기 전용)."""
    if not x_api_key:
        raise unauthorized("X-API-Key 가 필요합니다")
    key_hash = hash_api_key(x_api_key)
    admin = db.execute(
        select(Admin).where(Admin.api_key_hash == key_hash, Admin.deleted_at.is_(None))
    ).scalar_one_or_none()
    if not admin:
        raise unauthorized("유효하지 않은 API 키")
    return admin
