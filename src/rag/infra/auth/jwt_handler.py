from datetime import datetime, timedelta, timezone

import jwt


def create_access_token(
    data: dict,
    secret_key: str,
    expire_hours: int = 24,
) -> str:
    """生成 JWT access token"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(hours=expire_hours)
    to_encode["exp"] = expire
    return jwt.encode(to_encode, secret_key, algorithm="HS256")


def verify_token(token: str, secret_key: str) -> dict:
    """验证 JWT token，返回 payload；失败抛出异常"""
    return jwt.decode(token, secret_key, algorithms=["HS256"])
