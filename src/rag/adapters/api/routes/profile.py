from fastapi import APIRouter, Depends, HTTPException

from rag.adapters.api.dependencies import get_current_user
from rag.adapters.api.presenters.profile import ProfilePresenter
from rag.adapters.api.schemas.profile import UpdateProfileRequest
from rag.bootstrap.container import Container, get_container
from rag.domain.entities.user import User

router = APIRouter(prefix="/api/profile", tags=["profile"])


@router.get("")
async def get_profile(
    current_user: User = Depends(get_current_user),
    container: Container = Depends(get_container),
):
    profile = await container.profile_usecase.get(current_user.id)
    return ProfilePresenter.to_response(profile)


@router.put("")
async def update_profile(
    req: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    container: Container = Depends(get_container),
):
    try:
        profile = await container.profile_usecase.update(current_user.id, req.active_project_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return ProfilePresenter.to_response(profile)
