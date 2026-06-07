from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator


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

    @abstractmethod
    async def agenerate(self, prompt: str) -> str:
        """异步生成文本，不阻塞事件循环"""
        ...

    @abstractmethod
    async def astream(self, prompt: str) -> AsyncGenerator[str, None]:
        """异步流式生成文本，逐 token yield，不阻塞事件循环"""
        ...

    async def agenerate_json(self, prompt: str, schema: dict | None = None) -> dict:
        """异步生成结构化 JSON 输出，默认委托给 agenerate + 解析逻辑

        子类可覆盖此方法以提供更高效的实现。
        """
        raw = await self.agenerate(prompt)
        if not raw:
            raise ValueError("LLM 返回空内容，无法解析 JSON")
        return self._parse_json_output(raw)

    @staticmethod
    def _parse_json_output(raw: str) -> dict:
        """从原始文本中提取 JSON（供 agenerate_json 默认实现使用）"""
        import json
        import re

        # 1. 直接解析
        try:
            return json.loads(raw.strip())
        except json.JSONDecodeError:
            pass

        # 2. 提取 ```json ... ``` 代码块
        match = re.search(r"```(?:json)?\s*\n?(.*?)```", raw, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1).strip())
            except json.JSONDecodeError:
                pass

        # 3. 提取第一个 { 到最后一个 } 之间的内容
        start = raw.find("{")
        end = raw.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(raw[start : end + 1])
            except json.JSONDecodeError:
                pass

        # 4. 提取 [ ... ] 数组格式（包装为 dict）
        start = raw.find("[")
        end = raw.rfind("]")
        if start != -1 and end != -1 and end > start:
            try:
                items = json.loads(raw[start : end + 1])
                if isinstance(items, list):
                    return {"items": items}
            except json.JSONDecodeError:
                pass

        raise ValueError(f"无法解析 JSON，原始输出: {raw[:200]}")
