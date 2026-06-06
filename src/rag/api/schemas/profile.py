from pydantic import BaseModel


class UpdateProfileRequest(BaseModel):
    active_project_id: str | None = None


class ProfileResponse(BaseModel):
    id: int | None = None
    active_project_id: str | None = None
