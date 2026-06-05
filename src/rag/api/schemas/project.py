from pydantic import BaseModel


class CreateProjectRequest(BaseModel):
    name: str
    description: str = ""


class UpdateProjectRequest(BaseModel):
    name: str
    description: str = ""


class ProjectResponse(BaseModel):
    id: str
    name: str
    description: str
    created_at: str = ""
    updated_at: str = ""


class ProjectListResponse(BaseModel):
    projects: list[ProjectResponse]
