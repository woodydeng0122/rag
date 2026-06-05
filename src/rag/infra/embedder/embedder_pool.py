import threading
from collections import OrderedDict
from typing import Callable

from rag.domain.ports.embedder import EmbedderPort
from rag.domain.ports.embedder_pool import EmbedderPoolPort


class EmbedderPool(EmbedderPoolPort):
    """Embedder 实例缓存池 — 按模型名缓存，LRU 淘汰"""

    def __init__(
        self,
        factory: Callable[[str], EmbedderPort],
        max_size: int = 3,
    ):
        self._factory = factory
        self._max_size = max_size
        self._pool: OrderedDict[str, EmbedderPort] = OrderedDict()
        self._lock = threading.Lock()

    def get(self, model_name: str) -> EmbedderPort:
        """获取或创建 embedder 实例"""
        with self._lock:
            if model_name in self._pool:
                self._pool.move_to_end(model_name)
                return self._pool[model_name]

            embedder = self._factory(model_name)

            if len(self._pool) >= self._max_size:
                self._pool.popitem(last=False)

            self._pool[model_name] = embedder
            return embedder

    def is_loaded(self, model_name: str) -> bool:
        with self._lock:
            return model_name in self._pool

    def loaded_models(self) -> list[str]:
        with self._lock:
            return list(self._pool.keys())
