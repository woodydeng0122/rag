"""请求日志中间件 — 结构化打印每个请求的输入与输出（wide event 模式）"""

import json
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response, StreamingResponse

from rag.adapters.api.middleware.request_event import abuild_request_event
from rag.shared.logger import logger


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    为每个 HTTP 请求记录一条 wide event，包含完整的输入与输出。

    输入：method, path, path_params, query_params, request_body
    输出：status_code, duration_ms, response_body
    """

    # 不记录响应体的路径（避免大文件/二进制内容污染日志）
    _SKIP_BODY_PATHS = {"/docs", "/openapi.json", "/redoc"}

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # 跳过非 API 路径和文档路径
        path = request.url.path
        if path in self._SKIP_BODY_PATHS or not path.startswith("/api/"):
            return await call_next(request)

        start_time = time.monotonic()
        request_id = str(uuid.uuid4())[:8]

        # ── 构建输入 ──
        event = await abuild_request_event(request, request_id)

        # ── 调用 ──
        response = None
        error_msg = None
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as exc:
            status_code = 500
            error_msg = f"{type(exc).__name__}: {exc}"

        # ── 读取响应体 ──
        response_body = None
        if response is not None and not isinstance(response, StreamingResponse):
            content_type = response.headers.get("content-type", "")
            if "application/json" in content_type:
                try:
                    body = b""
                    async for chunk in response.body_iterator:
                        if isinstance(chunk, str):
                            body += chunk.encode("utf-8")
                        else:
                            body += chunk
                    response_body = json.loads(body)
                    # 重新构建响应（因为 body_iterator 已消费）
                    response = Response(
                        content=body,
                        status_code=response.status_code,
                        headers=dict(response.headers),
                        media_type=response.media_type,
                    )
                except Exception:
                    pass

        # ── 合并输出 ──
        event["status_code"] = status_code
        event["duration_ms"] = round((time.monotonic() - start_time) * 1000, 2)

        if error_msg:
            event["error"] = error_msg

        if response_body is not None:
            event["response_body"] = response_body

        # ── 一条 wide event ──
        if status_code >= 500:
            logger.error(event)
        elif status_code >= 400:
            logger.warning(event)
        else:
            logger.info(event)

        if response is None:
            raise RuntimeError(error_msg or "request failed with no response")

        return response
