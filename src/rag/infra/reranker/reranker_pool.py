import logging
import threading
from collections import OrderedDict

from sentence_transformers import CrossEncoder

from rag.domain.ports.reranker import RerankerPoolPort

logger = logging.getLogger(__name__)


class RerankerPool(RerankerPoolPort):
    """CrossEncoder 实例缓存池 — 按 model_path 缓存，LRU 淘汰"""

    def __init__(self, max_size: int = 3):
        self._max_size = max_size
        self._pool: OrderedDict[str, CrossEncoder] = OrderedDict()
        self._lock = threading.Lock()

    def get(self, model_path: str) -> CrossEncoder:
        """获取或创建 CrossEncoder 实例"""
        with self._lock:
            if model_path in self._pool:
                self._pool.move_to_end(model_path)
                return self._pool[model_path]

            logger.info("[RerankerPool] 加载 Reranker 模型: %s ...", model_path)
            reranker = CrossEncoder(model_path)
            logger.info("[RerankerPool] Reranker 模型加载完成: %s", model_path)

            if len(self._pool) >= self._max_size:
                evicted_path, _ = self._pool.popitem(last=False)
                logger.info("[RerankerPool] 淘汰缓存: %s", evicted_path)

            self._pool[model_path] = reranker
            return reranker

    def is_loaded(self, model_path: str) -> bool:
        with self._lock:
            return model_path in self._pool

    def loaded_models(self) -> list[str]:
        with self._lock:
            return list(self._pool.keys())
