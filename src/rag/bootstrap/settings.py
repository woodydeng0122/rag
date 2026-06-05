import os
import urllib.parse
from dataclasses import dataclass

from dotenv import load_dotenv
load_dotenv()

@dataclass
class Settings:
    """应用配置 — 从环境变量读取，提供默认值"""
    # LLM
    dashscope_api_key: str = ""
    dashscope_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    dashscope_model: str = "qwen3.6-plus-2026-04-02"

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
        if database_url:
            parsed = urllib.parse.urlparse(database_url)
            return cls(
                dashscope_api_key=os.getenv("DASHSCOPE_API_KEY", ""),
                db_host=parsed.hostname or "localhost",
                db_port=parsed.port or 5432,
                db_name=parsed.path.lstrip("/") or "rag-db",
                db_user=parsed.username or "admin",
                db_password=parsed.password or "password",
            )
        return cls(
            dashscope_api_key=os.getenv("DASHSCOPE_API_KEY", ""),
            db_host=os.getenv("DB_HOST", "localhost"),
            db_port=int(os.getenv("DB_PORT", "5434")),
            db_name=os.getenv("DB_NAME", "rag-db"),
            db_user=os.getenv("DB_USER", "admin"),
            db_password=os.getenv("DB_PASSWORD", "password"),
        )
