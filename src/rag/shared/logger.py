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


# ── 格式化 ─────────────────────────────────────────────────

def _format_input(event: dict, c) -> str:
    """格式化输入日志：→ method path [params]"""
    method = event.get("method", "")
    path = event.get("path", "")
    rid = event.get("request_id", "")
    params = event.get("params", {})
    query = event.get("query", "")

    method_str = f"{_METHOD_COLORS.get(method, c.WHITE)}{method}{c.RESET}" if c is not _NoColor else method
    path_str = f"{c.BOLD}{path}{c.RESET}" if c is not _NoColor else path

    parts = [f"{c.GRAY}→{c.RESET} {method_str} {path_str}"]

    if params:
        params_str = " ".join(f"{k}={v}" for k, v in params.items())
        parts.append(f"{c.CYAN}{params_str}{c.RESET}" if c is not _NoColor else params_str)

    if query:
        parts.append(f"{c.DIM}?{query}{c.RESET}" if c is not _NoColor else f"?{query}")

    parts.append(f"{c.DIM}[{rid}]{c.RESET}" if c is not _NoColor else f"[{rid}]")

    return " ".join(parts)


def _format_output(event: dict, c) -> str:
    """格式化输出日志：← status duration"""
    status_code = event.get("status_code", "")
    duration = event.get("duration_ms", "")
    rid = event.get("request_id", "")
    error = event.get("error", "")

    if status_code != "":
        sc = int(status_code)
        status_str = f"{_status_color(sc)}{sc}{c.RESET}" if c is not _NoColor else str(sc)
    else:
        status_str = "-"

    duration_str = f"{duration}ms" if duration != "" else "-"

    parts = [f"{c.GRAY}←{c.RESET} {status_str} {c.DIM}{duration_str}{c.RESET}"]

    if error:
        parts.append(f"{c.RED}{error}{c.RESET}" if c is not _NoColor else error)

    parts.append(f"{c.DIM}[{rid}]{c.RESET}" if c is not _NoColor else f"[{rid}]")

    return " ".join(parts)


def _format_simple(event: dict, c) -> str:
    """普通日志 — 一行式"""
    level = event.get("level", "info")
    timestamp = event.get("timestamp", "")
    message = event.get("message", "")

    level_colors = {"info": _C.GREEN, "error": _C.RED}
    level_color = level_colors.get(level, _C.WHITE)
    level_str = f"{level_color}{level.upper():<5}{c.RESET}" if c is not _NoColor else f"{level.upper():<5}"

    return f"{c.DIM}{timestamp}{c.RESET} {level_str} {message}"


# ── 格式化器 ───────────────────────────────────────────────

class _RequestFormatter(logging.Formatter):
    """智能格式化器：输入日志 → → 格式，输出日志 → ← 格式"""

    def __init__(self) -> None:
        super().__init__()
        self._use_color = _supports_color()

    def format(self, record: logging.LogRecord) -> str:
        c = _C if self._use_color else _NoColor

        if isinstance(record.msg, dict):
            event = dict(record.msg)
        else:
            event = {"message": str(record.msg)}

        event.setdefault("timestamp", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"))
        event.setdefault("level", record.levelname.lower())

        # 有 method+path → 输入日志
        if "method" in event and "path" in event:
            return _format_input(event, c)

        # 有 status_code → 输出日志
        if "status_code" in event:
            return _format_output(event, c)

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
