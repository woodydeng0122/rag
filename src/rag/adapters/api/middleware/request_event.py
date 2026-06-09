"""请求事件构建工具 — 从 Starlette Request 中提取结构化日志字段"""

import json

from starlette.requests import Request


def build_request_event(request: Request, request_id: str) -> dict:
    """从请求中提取基础事件字段：request_id, method, path, params, query, request_body"""
    event = {
        "request_id": request_id,
        "method": request.method,
        "path": request.url.path,
    }

    if request.path_params:
        event["params"] = dict(request.path_params)

    query = str(request.query_params)
    if query:
        event["query"] = query

    # 读取请求体（仅 JSON 请求）
    if request.method in ("POST", "PUT", "PATCH"):
        try:
            raw_body = request._body if hasattr(request, "_body") else None
            if raw_body is None:
                import asyncio
                raw_body = asyncio.get_event_loop().run_until_complete(request.body())
            if raw_body:
                content_type = request.headers.get("content-type", "")
                if "application/json" in content_type:
                    event["request_body"] = json.loads(raw_body)
                elif "multipart/form-data" not in content_type:
                    event["request_body"] = raw_body.decode("utf-8", errors="replace")[:500]
        except Exception:
            pass

    return event


async def abuild_request_event(request: Request, request_id: str) -> dict:
    """异步版：从请求中提取基础事件字段"""
    event = {
        "request_id": request_id,
        "method": request.method,
        "path": request.url.path,
    }

    if request.path_params:
        event["params"] = dict(request.path_params)

    query = str(request.query_params)
    if query:
        event["query"] = query

    # 读取请求体（仅 JSON 请求）
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

    return event
