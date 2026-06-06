## 概述

LLMPort 扩展 generate_json 方法，支持结构化 JSON 输出。DashScopeLLM 实现该方法，内置 JSON 解析和重试逻辑。

## 端口扩展

### LLMPort

```python
class LLMPort(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> str: ...

    @abstractmethod
    def generate_json(self, prompt: str, schema: dict | None = None) -> dict:
        """生成结构化 JSON 输出

        Args:
            prompt: 提示词（应包含"只输出 JSON"的指令）
            schema: 可选的 JSON Schema 描述，用于 prompt 增强和输出校验

        Returns:
            解析后的 dict

        Raises:
            ValueError: 重试后仍无法解析 JSON
        """
        ...
```

## Infra 实现：DashScopeLLM.generate_json

### 逻辑

1. 如果提供了 schema，在 prompt 末尾追加格式说明
2. 调用 `self.generate(prompt)` 获取原始文本
3. 尝试从原始文本中提取 JSON:
   - 优先尝试直接 `json.loads()`
   - 失败则提取 ```json ... ``` 代码块
   - 失败则提取第一个 `{` 到最后一个 `}` 之间的内容
4. 解析成功返回 dict
5. 解析失败重试（最多 2 次，重新调用 generate）
6. 重试仍失败抛出 ValueError

### schema 增强

当 schema 不为 None 时，在 prompt 末尾追加:

```
输出要求：
- 只输出合法 JSON，不要有其他内容
- 不要用 markdown 代码块包裹
- 格式说明：{schema 的自然语言描述}
```

当前阶段 schema 仅用于 prompt 增强，不做 JSON Schema 校验。

## 约束

- generate_json 依赖 generate 方法，不新增 API 调用逻辑
- 重试最多 2 次（共 3 次调用）
- 解析失败抛出 ValueError，由调用方决定如何处理
- 不做 JSON Schema 严格校验（后续可迭代）
