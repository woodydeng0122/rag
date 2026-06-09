import time
from contextlib import contextmanager
from collections.abc import Generator


@contextmanager
def measure(timings: dict[str, int], key: str) -> Generator[None, None, None]:
    """上下文管理器：测量代码块耗时（毫秒），结果写入 timings[key]"""
    start = time.monotonic()
    yield
    timings[key] = int((time.monotonic() - start) * 1000)
