"""统一响应模型 — 所有 API 返回 {code, message, result} 格式"""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")

# 成功码 — 与前端 ResultEnum.SUCCESS = 0 对齐
SUCCESS_CODE = 0
ERROR_CODE = -1
TIMEOUT_CODE = 401


class ApiResponse(BaseModel, Generic[T]):
    """统一响应包装

    前端约定格式（见 types/axios.d.ts Result 接口）：
    {
        "code": 0,          // 0=成功, -1=错误, 401=超时
        "message": "ok",
        "result": <T>
    }
    """

    code: int = SUCCESS_CODE
    message: str = "ok"
    result: T | None = None


def success(data: Any = None, message: str = "ok") -> dict:
    """构造成功响应"""
    return {"code": SUCCESS_CODE, "message": message, "result": data}


def error(message: str, code: int = ERROR_CODE) -> dict:
    """构造错误响应"""
    return {"code": code, "message": message, "result": None}
