from abc import ABC, abstractmethod


class MarkdownPreprocessorPort(ABC):
    """Markdown 预处理端口 — 解析扩展语法、展开引用，使分块器拿到纯净文本"""

    @abstractmethod
    def preprocess(self, text: str, source_path: str = "") -> str: ...
