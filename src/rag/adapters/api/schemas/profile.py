from pydantic import BaseModel


class UpdateProfileRequest(BaseModel):
    active_project_id: str | None = None


class ProfileResponse(BaseModel):
    id: str = ""
    user_id: str = ""
    active_project_id: str | None = None
