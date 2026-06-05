"""请求日志中间件 — 只记录每个接口的输入与输出"""

import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from rag.shared.logger import logger


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    为每个 HTTP 请求记录输入和输出。

    输入：method, path, path_params, query_params
    输出：status_code, duration_ms
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        start_time = time.monotonic()

        # ── 输入 ──
        input_event = {
            "request_id": str(uuid.uuid4())[:8],
            "method": request.method,
            "path": request.url.path,
        }
        query = str(request.query_params)
        if query:
            input_event["query"] = query

        # 记录路径参数（如 /projects/{project_id}/documents）
        if request.path_params:
            input_event["params"] = dict(request.path_params)

        logger.info(input_event)

        # ── 调用 ──
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as exc:
            logger.error({
                "request_id": input_event["request_id"],
                "status_code": 500,
                "duration_ms": round((time.monotonic() - start_time) * 1000, 2),
                "error": f"{type(exc).__name__}: {exc}",
            })
            raise

        # ── 输出 ──
        logger.info({
            "request_id": input_event["request_id"],
            "status_code": status_code,
            "duration_ms": round((time.monotonic() - start_time) * 1000, 2),
        })

        return response
