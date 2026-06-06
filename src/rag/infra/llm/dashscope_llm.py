import json
import logging
import re
import time
from openai import OpenAI, PermissionDeniedError
from rag.domain.ports.llm import LLMPort

logger = logging.getLogger(__name__)

_MAX_JSON_RETRIES = 2


class DashScopeLLM(LLMPort):
    """基于 DashScope (阿里云) 的 LLM 实现"""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1",
        model: str = "qwen3.6-plus-2026-04-02",
    ):
        self._api_key = api_key
        self._base_url = base_url
        self._model = model

    def generate(self, prompt: str) -> str:
        client = OpenAI(api_key=self._api_key, base_url=self._base_url)
        try:
            completion = client.chat.completions.create(
                model=self._model,
                messages=[{"role": "user", "content": prompt}],
                stream=True,
            )
        except PermissionDeniedError:
            logger.warning("DashScope 免费额度已用完。")
            return ""

        start = time.perf_counter()
        ttfb = None
        result = []
        for chunk in completion:
            content = chunk.choices[0].delta.content
            if content:
                if not ttfb:
                    ttfb = (time.perf_counter() - start) * 1000
                    logger.info("TTFB: %.2fms", ttfb)
                result.append(content)
        return "".join(result)

    def generate_json(self, prompt: str, schema: dict | None = None) -> dict:
        """生成结构化 JSON 输出，内置解析和重试"""
        enhanced_prompt = self._enhance_prompt(prompt, schema)

        for attempt in range(_MAX_JSON_RETRIES + 1):
            raw = self.generate(enhanced_prompt)
            if not raw:
                if attempt < _MAX_JSON_RETRIES:
                    logger.warning("generate_json: LLM 返回空，重试 %d/%d", attempt + 1, _MAX_JSON_RETRIES)
                    continue
                raise ValueError("LLM 返回空内容，无法解析 JSON")

            parsed = self._extract_json(raw)
            if parsed is not None:
                return parsed

            if attempt < _MAX_JSON_RETRIES:
                logger.warning("generate_json: JSON 解析失败，重试 %d/%d", attempt + 1, _MAX_JSON_RETRIES)

        raise ValueError(f"重试 {_MAX_JSON_RETRIES} 次后仍无法解析 JSON，原始输出: {raw[:200]}")

    @staticmethod
    def _enhance_prompt(prompt: str, schema: dict | None) -> str:
        """增强 prompt，追加 JSON 输出要求"""
        suffix = "\n\n输出要求：\n- 只输出合法 JSON，不要有其他内容\n- 不要用 markdown 代码块包裹"
        if schema:
            suffix += f"\n- 格式说明：{json.dumps(schema, ensure_ascii=False)}"
        return prompt + suffix

    @staticmethod
    def _extract_json(raw: str) -> dict | None:
        """从原始文本中提取 JSON：直接解析 → 代码块提取 → 大括号提取"""
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

        return None
