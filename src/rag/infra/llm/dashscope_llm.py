import logging
import time
from openai import OpenAI, PermissionDeniedError
from rag.domain.ports.llm import LLMPort

logger = logging.getLogger(__name__)


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
                print(content, end="", flush=True)
                result.append(content)
        print()
        return "".join(result)
