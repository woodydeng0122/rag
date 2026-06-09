import os
import sys
import urllib.parse
from dataclasses import dataclass

from dotenv import load_dotenv
load_dotenv()

@dataclass
class Settings:
    """应用配置 — 从环境变量读取，提供默认值"""
    # LLM
    dashscope_api_key: str = ""
    dashscope_base_url: str = ""
    dashscope_model: str = ""

    # 分块参数
    splitter_min_chars: int = 200
    splitter_max_chars: int = 2000

    # 数据库
    db_host: str = "localhost"
    db_port: int = 5434
    db_name: str = "rag-db"
    db_user: str = "admin"
    db_password: str = "password"

    @classmethod
    def from_env(cls) -> "Settings":
        """从环境变量读取配置，优先解析 DATABASE_URL"""
        database_url = os.getenv("DATABASE_URL", "")
        if not database_url:
            print("ERROR: 环境变量 DATABASE_URL 未设置，请在 .env 中配置", file=sys.stderr)
            sys.exit(1)
        parsed = urllib.parse.urlparse(database_url)
        return cls(
            dashscope_api_key=os.getenv("DASHSCOPE_API_KEY", ""),
            dashscope_base_url=os.getenv("DASHSCOPE_BASE_URL", ""),
            dashscope_model=os.getenv("DASHSCOPE_MODEL", ""),
            db_host=parsed.hostname or "localhost",
            db_port=parsed.port or 5432,
            db_name=parsed.path.lstrip("/") or "rag-db",
            db_user=parsed.username or "admin",
            db_password=parsed.password or "password",
        )
