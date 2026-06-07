from sentence_transformers import SentenceTransformer
from rag.domain.ports.embedder import EmbedderPort


class SentenceTransformerEmbedder(EmbedderPort):
    """基于 SentenceTransformer 的嵌入器实现"""

    def __init__(self, model_name: str = "BAAI/bge-small-zh-v1.5"):
        local_path = f"models/{model_name}" if not model_name.startswith("models/") else model_name
        self._model = SentenceTransformer(local_path, device="cpu")

    def embed(self, text: str | list[str]) -> list[list[float]]:
        if isinstance(text, str):
            text = [text]
        embeddings = self._model.encode(text, normalize_embeddings=True)
        return embeddings.tolist()
