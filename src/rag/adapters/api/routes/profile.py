from fastapi import APIRouter, Depends, HTTPException

from rag.adapters.api.presenters.profile import ProfilePresenter
from rag.adapters.api.schemas.profile import UpdateProfileRequest
from rag.bootstrap.container import Container, get_container

router = APIRouter(prefix="/api/profile", tags=["profile"])


@router.get("")
async def get_profile(
    container: Container = Depends(get_container),
):
    profile = await container.profile_usecase.get()
    return ProfilePresenter.to_response(profile)


@router.put("")
async def update_profile(
    req: UpdateProfileRequest,
    container: Container = Depends(get_container),
):
    try:
        profile = await container.profile_usecase.update(req.active_project_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return ProfilePresenter.to_response(profile)
