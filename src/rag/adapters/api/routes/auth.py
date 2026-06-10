from fastapi import APIRouter, Depends

from rag.adapters.api.dependencies import get_current_user
from rag.adapters.api.schemas.auth import LoginRequest, TokenResponse, UserInfo
from rag.adapters.api.schemas.response import ok
from rag.domain.entities.user import User

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login")
async def login(body: LoginRequest):
    from rag.bootstrap.container import get_container

    container = get_container()
    token = await container.auth_usecase.login(body.username, body.password)
    return ok(TokenResponse(access_token=token).model_dump())


@router.get("/me")
async def me(current_user: User = Depends(get_current_user)):
    return ok(
        UserInfo(
            id=current_user.id,
            username=current_user.username,
            created_at=current_user.created_at.isoformat() if current_user.created_at else None,
        ).model_dump()
    )
