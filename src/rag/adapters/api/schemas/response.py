"""统一响应模型 — 所有 API 返回 {code, message, result} 格式"""

# 成功码 — 与前端 ResultEnum.SUCCESS = 0 对齐
SUCCESS_CODE = 0
ERROR_CODE = -1
TIMEOUT_CODE = 401



def error(message: str, code: int = ERROR_CODE) -> dict:
    """构造错误响应"""
    return {"code": code, "message": message, "result": None}
