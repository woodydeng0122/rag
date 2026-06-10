from pydantic import BaseModel


class CreateUserRequest(BaseModel):
    username: str
    password: str


class UpdateUserRequest(BaseModel):
    password: str


class UserResponse(BaseModel):
    id: str
    username: str
    created_at: str | None = None
