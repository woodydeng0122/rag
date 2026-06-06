from abc import ABC, abstractmethod


class LLMPort(ABC):
    """LLM 端口 — 大语言模型生成的抽象"""

    @abstractmethod
    def generate(self, prompt: str) -> str: ...

    @abstractmethod
    def generate_json(self, prompt: str, schema: dict | None = None) -> dict:
        """生成结构化 JSON 输出

        Args:
            prompt: 提示词（应包含"只输出 JSON"的指令）
            schema: 可选的 JSON Schema 描述，用于 prompt 增强

        Returns:
            解析后的 dict

        Raises:
            ValueError: 重试后仍无法解析 JSON
        """
        ...
