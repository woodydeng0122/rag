from pydantic import BaseModel


class UpdateProfileRequest(BaseModel):
    active_project_id: str | None = None


class ProfileResponse(BaseModel):
    id: int = 1
    active_project_id: str | None = None
