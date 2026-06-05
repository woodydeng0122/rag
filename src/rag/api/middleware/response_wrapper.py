"""统一响应包装 + 请求日志中间件

自动将路由返回值包装为 {code, message, result} 格式，
同时为每个请求记录一条 wide event（结构化输入输出）。
"""

import json
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response, StreamingResponse

from rag.api.schemas.response import SUCCESS_CODE
from rag.shared.logger import logger


class ResponseWrapperMiddleware(BaseHTTPMiddleware):
    """
    自动包装 API 响应为统一格式 + 记录请求日志。

    响应包装规则：
    - 路径以 /api/ 开头的响应才会被包装
    - 已经是 {code, message, result} 格式的响应不会重复包装
    - HTTP 错误响应（4xx/5xx）由 exception handler 处理，此处不干预
    - 非 /api/ 路径（如 /health、/docs）不包装

    日志规则：
    - 每个 /api/ 请求记录一条 wide event，包含输入和输出
    - 输入：method, path, params, query, request_body
    - 输出：status_code, duration_ms, response_body
    """

    _SKIP_LOG_PATHS = {"/docs", "/openapi.json", "/redoc"}

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        path = request.url.path
        is_api = path.startswith("/api/")
        should_log = is_api and path not in self._SKIP_LOG_PATHS

        start_time = time.monotonic() if should_log else 0
        request_id = str(uuid.uuid4())[:8] if should_log else ""

        # ── 构建日志输入 ──
        event = {}
        if should_log:
            event = {
                "request_id": request_id,
                "method": request.method,
                "path": path,
            }
            if request.path_params:
                event["params"] = dict(request.path_params)
            query = str(request.query_params)
            if query:
                event["query"] = query

            # 读取请求体
            if request.method in ("POST", "PUT", "PATCH"):
                try:
                    raw_body = await request.body()
                    if raw_body:
                        content_type = request.headers.get("content-type", "")
                        if "application/json" in content_type:
                            event["request_body"] = json.loads(raw_body)
                        elif "multipart/form-data" not in content_type:
                            event["request_body"] = raw_body.decode("utf-8", errors="replace")[:500]
                except Exception:
                    pass

        # ── 调用路由 ──
        response = None
        error_msg = None
        try:
            response = await call_next(request)
        except Exception as exc:
            error_msg = f"{type(exc).__name__}: {exc}"

        # ── 读取 + 包装响应体 ──
        status_code = response.status_code if response else 500
        wrapped_body_bytes = None

        if is_api and response is not None and not isinstance(response, StreamingResponse):
            content_type = response.headers.get("content-type", "")
            if "application/json" in content_type:
                # 读取原始响应体
                body = b""
                async for chunk in response.body_iterator:
                    if isinstance(chunk, str):
                        body += chunk.encode("utf-8")
                    else:
                        body += chunk

                try:
                    data = json.loads(body)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    data = None

                if data is not None:
                    # 包装为统一格式
                    if isinstance(data, dict) and "code" in data and "result" in data:
                        wrapped = data
                    else:
                        wrapped = {"code": SUCCESS_CODE, "message": "ok", "result": data}

                    wrapped_body_bytes = json.dumps(wrapped, ensure_ascii=False).encode("utf-8")

                    # 记录响应体到日志（列表型只记摘要）
                    if should_log:
                        if isinstance(data, list):
                            event["result_count"] = len(data)
                            event["response_body"] = data[:1] if data else []
                        else:
                            event["response_body"] = data

        # ── 构建最终响应 ──
        if wrapped_body_bytes is not None:
            new_headers = dict(response.headers)
            new_headers.pop("content-length", None)
            new_headers.pop("transfer-encoding", None)
            final_response = Response(
                content=wrapped_body_bytes,
                status_code=status_code,
                headers=new_headers,
                media_type="application/json",
            )
        elif response is not None:
            final_response = response
        else:
            raise RuntimeError(error_msg or "request failed with no response")

        # ── 记录日志 ──
        if should_log:
            event["status_code"] = status_code
            event["duration_ms"] = round((time.monotonic() - start_time) * 1000, 2)
            if error_msg:
                event["error"] = error_msg

            if status_code >= 500:
                logger.error(event)
            elif status_code >= 400:
                logger.warning(event)
            else:
                logger.info(event)

        return final_response
