from sentence_transformers import SentenceTransformer
from rag.domain.ports.embedder import EmbedderPort


class SentenceTransformerEmbedder(EmbedderPort):
    """基于 SentenceTransformer 的嵌入器实现"""

    def __init__(self, model_name: str = "models/BAAI/bge-small-zh-v1.5"):
        self._model = SentenceTransformer(model_name, device="cpu")

    def embed(self, text: str | list[str]) -> list[list[float]]:
        if isinstance(text, str):
            text = [text]
        embeddings = self._model.encode(text, normalize_embeddings=True)
        return embeddings.tolist()
