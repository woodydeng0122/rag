from fastapi import APIRouter, Depends, HTTPException

from rag.api.schemas.profile import UpdateProfileRequest, ProfileResponse
from rag.domain.entities.profile import Profile
from rag.bootstrap.container import Container, get_container

router = APIRouter(prefix="/api/profile", tags=["profile"])


def _profile_to_response(p: Profile) -> ProfileResponse:
    return ProfileResponse(
        id=p.id,
        active_project_id=p.active_project_id if p.active_project_id else None,
    )


@router.get("", response_model=ProfileResponse)
async def get_profile(
    container: Container = Depends(get_container),
):
    profile = await container.profile_usecase.get()
    return _profile_to_response(profile)


@router.put("", response_model=ProfileResponse)
async def update_profile(
    req: UpdateProfileRequest,
    container: Container = Depends(get_container),
):
    try:
        profile = await container.profile_usecase.update(req.active_project_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return _profile_to_response(profile)
