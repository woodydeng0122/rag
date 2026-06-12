from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from rag.domain.entities.user import User

_bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> User:
    """FastAPI 认证依赖 — 从 Bearer Token 解析当前用户"""
    if credentials is None:
        raise HTTPException(status_code=401, detail="未提供认证凭据")

    from rag.bootstrap.container import get_container

    container = get_container()
    auth_usecase = container.auth_usecase
    try:
        user = await auth_usecase.get_current_user(credentials.credentials)
    except ValueError:
        raise HTTPException(status_code=401, detail="无效的认证凭据")
    return user
