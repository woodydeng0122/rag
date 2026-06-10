from fastapi import APIRouter, Depends

from rag.adapters.api.dependencies import get_current_user
from rag.adapters.api.schemas.user import CreateUserRequest, UpdateUserRequest
from rag.adapters.api.schemas.response import ok
from rag.adapters.api.presenters.user import present_user
from rag.domain.entities.user import User

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("")
async def list_users(_current_user: User = Depends(get_current_user)):
    from rag.bootstrap.container import get_container

    container = get_container()
    users = await container.auth_usecase._user_repo.list_all()
    return ok([present_user(u) for u in users])


@router.post("", status_code=201)
async def create_user(body: CreateUserRequest, _current_user: User = Depends(get_current_user)):
    from rag.bootstrap.container import get_container
    from rag.infra.auth.password import hash_password

    container = get_container()
    user_repo = container.auth_usecase._user_repo

    existing = await user_repo.get_by_username(body.username)
    if existing is not None:
        raise ValueError("用户名已存在")

    user = await user_repo.create(body.username, hash_password(body.password))
    return ok(present_user(user))


@router.put("/{user_id}")
async def update_user(user_id: str, body: UpdateUserRequest, _current_user: User = Depends(get_current_user)):
    from rag.bootstrap.container import get_container
    from rag.infra.auth.password import hash_password

    container = get_container()
    user_repo = container.auth_usecase._user_repo

    user = await user_repo.get_by_id(user_id)
    if user is None:
        raise ValueError("用户不存在")

    user = await user_repo.update_password(user_id, hash_password(body.password))
    return ok(present_user(user))


@router.delete("/{user_id}", status_code=204)
async def delete_user(user_id: str, current_user: User = Depends(get_current_user)):
    from rag.bootstrap.container import get_container

    if current_user.id == user_id:
        raise ValueError("不能删除当前登录用户")

    container = get_container()
    user_repo = container.auth_usecase._user_repo

    user = await user_repo.get_by_id(user_id)
    if user is None:
        raise ValueError("用户不存在")

    await user_repo.delete(user_id)
