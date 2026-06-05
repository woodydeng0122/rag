"""全局单例日志器 — 美观输出接口的输入与输出"""

import json
import logging
import sys
from datetime import datetime, timezone


# ── ANSI 颜色 ──────────────────────────────────────────────

class _C:
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"
    GREEN   = "\033[32m"
    YELLOW  = "\033[33m"
    RED     = "\033[31m"
    CYAN    = "\033[36m"
    MAGENTA = "\033[35m"
    BLUE    = "\033[34m"
    WHITE   = "\033[37m"
    GRAY    = "\033[90m"


def _supports_color() -> bool:
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


# ── 颜色映射 ───────────────────────────────────────────────

_METHOD_COLORS = {
    "GET": _C.GREEN, "POST": _C.CYAN, "PUT": _C.BLUE,
    "PATCH": _C.MAGENTA, "DELETE": _C.RED,
}

def _status_color(code: int) -> str:
    if code < 300:   return _C.GREEN
    if code < 400:   return _C.CYAN
    if code < 500:   return _C.YELLOW
    return _C.RED


# ── 无颜色占位类 ───────────────────────────────────────────

class _NoColor:
    RESET = BOLD = DIM = GREEN = YELLOW = RED = CYAN = ""
    MAGENTA = BLUE = WHITE = GRAY = ""


# ── 截断工具 ───────────────────────────────────────────────

def _truncate(obj, max_str=200, max_list=5):
    """递归截断大对象，避免日志过长"""
    if isinstance(obj, str):
        if len(obj) > max_str:
            return obj[:max_str] + f"... ({len(obj)} chars)"
        return obj
    if isinstance(obj, list):
        if len(obj) > max_list:
            truncated = [_truncate(item, max_str, max_list) for item in obj[:max_list]]
            return truncated + [f"... +{len(obj) - max_list} more"]
        return [_truncate(item, max_str, max_list) for item in obj]
    if isinstance(obj, dict):
        return {k: _truncate(v, max_str, max_list) for k, v in obj.items()}
    return obj


# ── 格式化 ─────────────────────────────────────────────────

def _format_wide_event(event: dict, c) -> str:
    """格式化 wide event：→ method path [params] ← status duration {body}"""
    method = event.get("method", "")
    path = event.get("path", "")
    rid = event.get("request_id", "")
    params = event.get("params", {})
    query = event.get("query", "")
    status_code = event.get("status_code")
    duration_ms = event.get("duration_ms")
    error = event.get("error", "")
    request_body = event.get("request_body")
    result_count = event.get("result_count")
    response_body = event.get("response_body")

    # ── 输入行 ──
    method_str = f"{_METHOD_COLORS.get(method, c.WHITE)}{method}{c.RESET}" if c is not _NoColor else method
    path_str = f"{c.BOLD}{path}{c.RESET}" if c is not _NoColor else path

    parts = [f"{c.GRAY}→{c.RESET} {method_str} {path_str}"]

    if params:
        params_str = " ".join(f"{k}={v}" for k, v in params.items())
        parts.append(f"{c.CYAN}{params_str}{c.RESET}" if c is not _NoColor else params_str)

    if query:
        parts.append(f"{c.DIM}?{query}{c.RESET}" if c is not _NoColor else f"?{query}")

    parts.append(f"{c.DIM}[{rid}]{c.RESET}" if c is not _NoColor else f"[{rid}]")

    input_line = " ".join(parts)

    # ── 请求体 ──
    body_lines = []
    if request_body is not None:
        truncated = _truncate(request_body)
        body_str = json.dumps(truncated, ensure_ascii=False, indent=2)
        for line in body_str.split("\n"):
            body_lines.append(f"  {c.DIM}{line}{c.RESET}" if c is not _NoColor else f"  {line}")

    # ── 输出行 ──
    if status_code is not None:
        sc = int(status_code)
        status_str = f"{_status_color(sc)}{sc}{c.RESET}" if c is not _NoColor else str(sc)
    else:
        status_str = "-"

    duration_str = f"{duration_ms}ms" if duration_ms is not None else "-"
    output_parts = [f"{c.GRAY}←{c.RESET} {status_str} {c.DIM}{duration_str}{c.RESET}"]

    if result_count is not None:
        output_parts.append(f"{c.CYAN}items={result_count}{c.RESET}" if c is not _NoColor else f"items={result_count}")

    if error:
        output_parts.append(f"{c.RED}{error}{c.RESET}" if c is not _NoColor else error)

    output_parts.append(f"{c.DIM}[{rid}]{c.RESET}" if c is not _NoColor else f"[{rid}]")

    output_line = " ".join(output_parts)

    # ── 响应体 ──
    resp_lines = []
    if response_body is not None:
        if result_count is not None:
            # 列表型响应：只显示首项预览 + 总数
            if response_body:
                preview = _truncate(response_body[0], max_str=120, max_list=2)
                preview_str = json.dumps(preview, ensure_ascii=False, indent=2)
                first_line = f"  {c.DIM}[0] {preview_str.split(chr(10))[0]}{c.RESET}" if c is not _NoColor else f"  [0] {preview_str.split(chr(10))[0]}"
                resp_lines.append(first_line)
                if result_count > 1:
                    more = f"  {c.DIM}... +{result_count - 1} more items{c.RESET}" if c is not _NoColor else f"  ... +{result_count - 1} more items"
                    resp_lines.append(more)
            else:
                resp_lines.append(f"  {c.DIM}[] (empty list){c.RESET}" if c is not _NoColor else "  [] (empty list)")
        else:
            truncated = _truncate(response_body)
            body_str = json.dumps(truncated, ensure_ascii=False, indent=2)
            for line in body_str.split("\n"):
                resp_lines.append(f"  {c.DIM}{line}{c.RESET}" if c is not _NoColor else f"  {line}")

    # ── 组装 ──
    lines = [input_line]
    lines.extend(body_lines)
    lines.append(output_line)
    lines.extend(resp_lines)

    return "\n".join(lines)


def _format_simple(event: dict, c) -> str:
    """普通日志 — 一行式"""
    level = event.get("level", "info")
    timestamp = event.get("timestamp", "")
    message = event.get("message", "")

    level_colors = {"info": _C.GREEN, "warning": _C.YELLOW, "error": _C.RED}
    level_color = level_colors.get(level, _C.WHITE)
    level_str = f"{level_color}{level.upper():<7}{c.RESET}" if c is not _NoColor else f"{level.upper():<7}"

    # 如果有 extra 字段，也打印出来
    extra_keys = set(event.keys()) - {"level", "timestamp", "message"}
    extra_parts = []
    for k in sorted(extra_keys):
        v = event[k]
        extra_parts.append(f"{k}={v}")

    extra_str = f" {c.DIM}[{' '.join(extra_parts)}]{c.RESET}" if extra_parts else ""

    return f"{c.DIM}{timestamp}{c.RESET} {level_str} {message}{extra_str}"


# ── 格式化器 ───────────────────────────────────────────────

class _RequestFormatter(logging.Formatter):
    """智能格式化器：wide event → 结构化多行，普通日志 → 一行式"""

    def __init__(self) -> None:
        super().__init__()
        self._use_color = _supports_color()

    def format(self, record: logging.LogRecord) -> str:
        c = _C if self._use_color else _NoColor

        if isinstance(record.msg, dict):
            event = dict(record.msg)
        else:
            event = {"message": str(record.msg)}

        # 合并 extra 字段
        if hasattr(record, "extra") and isinstance(record.extra, dict):
            event.update(record.extra)

        event.setdefault("timestamp", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"))
        event.setdefault("level", record.levelname.lower())

        # wide event：有 method+path 或 status_code
        if "method" in event or "status_code" in event:
            return _format_wide_event(event, c)

        return _format_simple(event, c)


# ── 构建日志器 ─────────────────────────────────────────────

def _build_logger() -> logging.Logger:
    logger = logging.getLogger("rag")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(_RequestFormatter())
        logger.addHandler(handler)

    logger.propagate = False
    return logger


# 模块级单例
logger = _build_logger()
