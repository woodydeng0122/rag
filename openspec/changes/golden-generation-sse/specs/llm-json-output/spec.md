## ADDED Requirements

### Requirement: LLMPort astream method
LLMPort 接口 SHALL 新增 `astream` 异步流式生成方法，逐 token yield 输出。

```python
@abstractmethod
async def astream(self, prompt: str) -> AsyncGenerator[str, None]: ...
```

#### Scenario: 流式输出
- **WHEN** 调用 `astream(prompt)`
- **THEN** 逐 token yield LLM 输出内容，直到输出结束

#### Scenario: API 额度用完
- **WHEN** DashScope 返回 PermissionDeniedError
- **THEN** 生成器结束，不 yield 任何内容

### Requirement: DashScopeLLM astream implementation
DashScopeLLM SHALL 使用 AsyncOpenAI 客户端实现 `astream` 方法。

#### Scenario: 流式调用
- **WHEN** 调用 `astream(prompt)`
- **THEN** 使用 `self._async_client.chat.completions.create(stream=True)` 创建流式完成，`async for` 遍历逐 token yield
