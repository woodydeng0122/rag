from rag.domain.entities.chunk import Chunk
from rag.domain.ports.splitter import SplitterPort


class FixedSizeSplitter(SplitterPort):
    """固定大小分块策略实现"""

    def __init__(self, chunk_size: int = 500, overlap: int = 50):
        self._chunk_size = chunk_size
        self._overlap = overlap

    def split(self, text: str, **kwargs) -> list[Chunk]:
        chunk_size = kwargs.get("chunk_size", self._chunk_size)
        overlap = kwargs.get("overlap", self._overlap)
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk_text = text[start:end]
            chunks.append(Chunk(id="", content=chunk_text))
            start = end - overlap
        return chunks
