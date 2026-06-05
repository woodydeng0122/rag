"""统一响应包装中间件 — 自动将路由返回值包装为 {code, message, result} 格式"""

import json

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response, StreamingResponse

from rag.api.schemas.response import SUCCESS_CODE


class ResponseWrapperMiddleware(BaseHTTPMiddleware):
    """
    自动包装 API 响应为统一格式。

    规则：
    - 路径以 /api/ 开头的响应才会被包装
    - 已经是 {code, message, result} 格式的响应不会重复包装
    - HTTP 错误响应（4xx/5xx）由 exception handler 处理，此处不干预
    - 非 /api/ 路径（如 /health、/docs）不包装
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        response = await call_next(request)

        # 只包装 /api/ 路径的 JSON 响应
        if not request.url.path.startswith("/api/"):
            return response

        # 流式响应或非 JSON 响应不包装
        if isinstance(response, StreamingResponse):
            return response

        content_type = response.headers.get("content-type", "")
        if "application/json" not in content_type:
            return response

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
            return Response(
                content=body,
                status_code=response.status_code,
                media_type=response.media_type,
            )

        # 已经是统一格式则不重复包装
        if isinstance(data, dict) and "code" in data and "result" in data:
            wrapped_body = json.dumps(data, ensure_ascii=False)
        else:
            # 包装为统一格式
            wrapped = {
                "code": SUCCESS_CODE,
                "message": "ok",
                "result": data,
            }
            wrapped_body = json.dumps(wrapped, ensure_ascii=False)

        # 构建新响应头：去掉 Content-Length（由 Response 自动重算）
        new_headers = dict(response.headers)
        new_headers.pop("content-length", None)
        new_headers.pop("transfer-encoding", None)

        return Response(
            content=wrapped_body,
            status_code=response.status_code,
            headers=new_headers,
            media_type="application/json",
        )
