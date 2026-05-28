"""JWT 認證中介層"""

import os
from functools import wraps

import jwt
from flask import request, g

from exceptions import AuthError


JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"


def extract_token_from_header():
    """從 Authorization header 提取 Bearer token"""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    return auth_header[7:]


def verify_jwt(token: str) -> dict:
    """驗證 JWT token 並回傳 payload"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthError("Token 已過期", "TOKEN_EXPIRED")
    except jwt.InvalidTokenError:
        raise AuthError("無效的 token", "TOKEN_INVALID")


def require_auth(f):
    """需要認證的 API decorator"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = extract_token_from_header()
        if not token:
            raise AuthError("未提供認證 token", "TOKEN_MISSING")

        payload = verify_jwt(token)

        # 確認是 access token（非 refresh token）
        if payload.get("type") == "refresh":
            raise AuthError("請使用 Access Token", "WRONG_TOKEN_TYPE")

        # 注入使用者資訊到 Flask request context
        g.user = {
            "id": payload.get("sub"),
            "username": payload.get("username"),
            "firestore_doc_id": payload.get("firestore_doc_id")
        }
        return f(*args, **kwargs)
    return decorated
