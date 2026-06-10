from dataclasses import dataclass
from datetime import datetime


@dataclass
class User:
    """用户实体"""

    id: str = ""
    username: str = ""
    password_hash: str = ""
    created_at: datetime | None = None
