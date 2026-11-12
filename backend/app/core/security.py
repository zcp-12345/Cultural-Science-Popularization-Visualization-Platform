"""密码哈希与 JWT 签发/校验（M3 用户系统）。"""
from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

from app.core.config import get_settings

_password_hasher = PasswordHasher()


def hash_password(plain: str) -> str:
    return _password_hasher.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return _password_hasher.verify(hashed, plain)
    except (VerifyMismatchError, InvalidHashError):
        return False


def _create_token(subject: str, token_type: str, ttl: timedelta) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "type": token_type,
        "iat": now,
        "exp": now + ttl,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def create_access_token(user_id: int) -> str:
    settings = get_settings()
    return _create_token(str(user_id), "access", timedelta(minutes=settings.jwt_access_ttl_minutes))


def create_refresh_token(user_id: int) -> str:
    settings = get_settings()
    return _create_token(str(user_id), "refresh", timedelta(days=settings.jwt_refresh_ttl_days))


def decode_token(token: str, expected_type: str) -> str:
    """校验 JWT 并返回 subject（user_id 字符串）。

    非法签名 / 过期 / 类型不符 / 缺 sub 均抛 `jwt.PyJWTError` 子类。
    """
    settings = get_settings()
    payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    if payload.get("type") != expected_type:
        raise jwt.InvalidTokenError("token 类型不符")
    subject = payload.get("sub")
    if not subject:
        raise jwt.InvalidTokenError("token 缺少 sub")
    return subject
