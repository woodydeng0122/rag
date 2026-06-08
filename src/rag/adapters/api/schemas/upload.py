from pydantic import BaseModel


class UploadResponse(BaseModel):
    documents: list[dict]
    count: int
