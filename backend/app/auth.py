"""JWT authentication utilities."""

import logging
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from jose import JWTError, jwt

logger = logging.getLogger(__name__)

_RAW_SECRET = os.getenv("JWT_SECRET_KEY", "")
if not _RAW_SECRET or _RAW_SECRET in ("dev-secret-change-me", "change-me-to-a-random-string", "change-me-in-production"):
    _SECRET = secrets.token_urlsafe(48)
    logger.warning(
        "JWT_SECRET_KEY 未设置或使用了默认值！已生成随机密钥。"
        "生产环境请务必在环境变量中设置 JWT_SECRET_KEY。"
    )
else:
    _SECRET = _RAW_SECRET

_ALGORITHM = "HS256"
_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "120"))


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=_EXPIRE_MINUTES))
    to_encode["exp"] = expire
    return jwt.encode(to_encode, _SECRET, algorithm=_ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, _SECRET, algorithms=[_ALGORITHM])
    except JWTError:
        return None
