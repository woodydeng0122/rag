from dataclasses import dataclass
from datetime import datetime


@dataclass
class Project:
    """项目实体 — 一个项目包含多文档"""
    id: str = ""
    name: str = ""
    description: str = ""
    created_at: datetime | None = None
    updated_at: datetime | None = None
