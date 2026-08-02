"""보안 유틸 — 비밀번호 해시, 이름 암호화/HMAC, JWT, API 키."""
import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.config import settings

_AES_KEY = bytes.fromhex(settings.name_aes_key)
_HMAC_KEY = bytes.fromhex(settings.name_hmac_key)


# --- 비밀번호 (bcrypt) ---
def hash_password(raw: str) -> str:
    return bcrypt.hashpw(raw.encode(), bcrypt.gensalt()).decode()


def verify_password(raw: str, hashed: str) -> bool:
    return bcrypt.checkpw(raw.encode(), hashed.encode())


def initial_user_password(student_number: str) -> str:
    """user 초기 비밀번호 = '00' + 학번 4자리."""
    return "00" + student_number


# --- 필드 암호화 (AES-GCM) ---
def aes_encrypt(plain: str) -> bytes:
    """랜덤 nonce(12B) + 암호문. 같은 키를 여러 필드에 써도 nonce가 매번 달라 안전."""
    nonce = os.urandom(12)
    ct = AESGCM(_AES_KEY).encrypt(nonce, plain.encode(), None)
    return nonce + ct


def aes_decrypt(blob: bytes) -> str:
    nonce, ct = blob[:12], blob[12:]
    return AESGCM(_AES_KEY).decrypt(nonce, ct, None).decode()


# --- 이름 암호화 (AES-GCM) + 조회용 HMAC ---
def encrypt_name(name: str) -> bytes:
    # 조회는 name_hmac으로 하므로 비결정 암호화로 충분.
    return aes_encrypt(name)


def decrypt_name(blob: bytes) -> str:
    return aes_decrypt(blob)


def name_hmac(name: str) -> str:
    """이름 조회·유니크용 HMAC-SHA256 hex. 앞뒤 공백 제거 후 계산."""
    return hmac.new(_HMAC_KEY, name.strip().encode(), hashlib.sha256).hexdigest()


# --- JWT ---
def create_access_token(sub: int, actor: str, minutes: int, extra: dict | None = None) -> tuple[str, datetime]:
    exp = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    payload = {"sub": str(sub), "actor": actor, "exp": exp}
    if extra:
        payload.update(extra)
    token = jwt.encode(payload, settings.jwt_secret, algorithm="HS256")
    return token, exp


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])


# --- MCP API 키 ---
def hash_api_key(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()
