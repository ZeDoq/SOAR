"""Authentication API routes."""

import re
import time
from collections import defaultdict
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Header

from ..auth import create_access_token, decode_token, hash_password, verify_password
from ..storage import create_user, get_user_by_username

router = APIRouter(prefix="/auth", tags=["auth"])

# 简易登录限速（进程内存，重启清零）
_login_attempts: dict = defaultdict(list)
_MAX_ATTEMPTS = 10
_WINDOW_SECONDS = 300


def _check_rate_limit(key: str) -> None:
    now = time.time()
    attempts = _login_attempts[key]
    # 清除过期记录
    _login_attempts[key] = [t for t in attempts if now - t < _WINDOW_SECONDS]
    if len(_login_attempts[key]) >= _MAX_ATTEMPTS:
        raise HTTPException(status_code=429, detail="登录尝试过于频繁，请 5 分钟后重试")
    _login_attempts[key].append(now)


def _validate_password(password: str) -> None:
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="密码长度至少 8 位")
    if not re.search(r"[a-zA-Z]", password):
        raise HTTPException(status_code=400, detail="密码必须包含字母")
    if not re.search(r"\d", password):
        raise HTTPException(status_code=400, detail="密码必须包含数字")


def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    """
    从 Authorization 头提取当前用户。
    必须通过 Depends() 注入到需要认证的路由。
    无效或缺失 token 直接返回 401。
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未提供认证凭据")
    token = authorization.split(" ", 1)[1]
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token 无效或已过期")
    return {"id": payload.get("sub"), "username": payload.get("username")}


@router.post("/register")
def register(body: dict) -> dict:
    username = (body.get("username") or "").strip()
    password = body.get("password") or ""

    if not username or not password:
        raise HTTPException(status_code=400, detail="用户名和密码不能为空")
    if len(username) < 3 or len(username) > 32:
        raise HTTPException(status_code=400, detail="用户名长度需在 3-32 之间")
    if not re.match(r"^[a-zA-Z0-9_-]+$", username):
        raise HTTPException(status_code=400, detail="用户名只能包含字母、数字、下划线、连字符")

    _validate_password(password)

    existing = get_user_by_username(username)
    if existing:
        raise HTTPException(status_code=409, detail="用户名已存在")
    user = create_user(username, hash_password(password))
    return {"user": {"id": user["id"], "username": user["username"]}}


@router.post("/login")
def login(body: dict) -> dict:
    username = (body.get("username") or "").strip()
    password = body.get("password") or ""

    if not username or not password:
        raise HTTPException(status_code=400, detail="用户名和密码不能为空")

    _check_rate_limit(username)

    user = get_user_by_username(username)
    if not user or not verify_password(password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    token = create_access_token({"sub": str(user["id"]), "username": user["username"]})
    return {"access_token": token, "token_type": "bearer"}
