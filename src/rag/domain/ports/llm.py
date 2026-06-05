from abc import ABC, abstractmethod


class LLMPort(ABC):
    """LLM 端口 — 大语言模型生成的抽象"""

    @abstractmethod
    def generate(self, prompt: str) -> str: ...
