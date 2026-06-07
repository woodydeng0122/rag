## Context

当前黄金数据集生成采用 `asyncio.create_task` 启动后台协程，串行调用同步 LLM 接口。前端提交任务后只能轮询任务状态，无法看到生成过程。LLM 调用已改为异步（`agenerate`/`agenerate_json`），但仍是一次性返回完整结果，不支持流式输出。

前端 `GoldenDataset.vue` 使用 Ant Design Vue，已有生成弹窗但只展示提交表单，无过程面板。

## Goals / Non-Goals

**Goals:**
- 通过 SSE 实时推送生成过程（进度、LLM 流式 token、生成结果）
- 支持任务暂停/继续/取消/重试失败项
- 前端内嵌生成面板，生成过程中用户可继续操作表格
- 断线重连后从 DB 恢复最新进度

**Non-Goals:**
- 不做 SSE 历史事件补发（断线后只恢复进度，不回放流式内容）
- 不做 LLM 调用中途暂停（只在每条问题处理完后检查暂停标志）
- 不做生成去重
- 不做成本/配额控制
- 不做 WebSocket 方案

## Decisions

### D1: SSE 而非 WebSocket

**选择**: Server-Sent Events

**理由**:
- 生成过程是单向推送（后端→前端），不需要双向通信
- FastAPI 原生支持 `StreamingResponse`，无需额外依赖
- 前端 `EventSource` API 简单，浏览器自动重连
- WebSocket 过重，需要额外处理心跳、重连逻辑

**替代方案**: WebSocket — 双向通信能力未被利用，增加复杂度

### D2: SSE 连接生命周期 — 方案 A

**选择**: `POST /generate` 返回 `task_id`，前端开 `GET /generation-tasks/{tid}/stream` 监听

**理由**:
- 职责分离：创建任务和消费事件是独立操作
- 支持页面刷新后重新连接（只需 task_id）
- 多个客户端可同时监听同一任务

**替代方案**: POST 本身返回 SSE 流 — 无法刷新重连

### D3: GenerationTaskRunner 事件驱动架构

**选择**: 将 `_run_generation` 重构为异步生成器，每步 yield 事件字典

```
GenerationTaskRunner.run() → AsyncGenerator[dict]
  yield {"type": "progress", ...}
  yield {"type": "llm_token", ...}
  yield {"type": "result", ...}
```

SSE 端点消费此生成器，将事件格式化为 SSE 推送。

**理由**:
- 生成逻辑与传输层解耦（Runner 不关心 SSE）
- 可测试性好（可直接消费生成器验证事件序列）
- 符合 Clean Architecture：Use Case 层产出事件，Interface Adapter 层负责传输

### D4: 暂停/取消控制 — asyncio.Event

**选择**: Runner 持有 `pause_event: asyncio.Event`（默认 set）和 `cancel_flag: asyncio.Event`（默认 clear）

- 暂停: `pause_event.clear()` → Runner 在每条问题处理完后 `await pause_event.wait()`
- 继续: `pause_event.set()` → 阻塞的 wait 立即返回
- 取消: `cancel_flag.set()` → Runner 在检查点检查并退出循环

**理由**:
- `asyncio.Event` 是协程原生同步原语，无需额外依赖
- 暂停粒度为"每条问题处理完"，避免半截状态
- Runner 实例由 `TaskManager` 管理，API 层通过 TaskManager 操作

### D5: TaskManager 管理活跃任务

**选择**: 新增 `TaskManager` 单例，管理所有活跃的 `GenerationTaskRunner` 实例

```python
class TaskManager:
    _runners: dict[str, GenerationTaskRunner]  # task_id → runner

    def register(self, task_id, runner): ...
    def get(self, task_id) -> Runner | None: ...
    def remove(self, task_id): ...
```

**理由**:
- API 层需要通过 task_id 找到 Runner 来执行暂停/继续/取消
- Runner 不应存储在 DB 中（包含 asyncio.Event 等不可序列化对象）
- TaskManager 在 bootstrap/container 中注册为单例

### D6: LLMPort.astream 流式输出

**选择**: 新增 `astream(prompt) -> AsyncGenerator[str, None]` 方法

```python
# LLMPort
@abstractmethod
async def astream(self, prompt: str) -> AsyncGenerator[str, None]: ...

# DashScopeLLM
async def astream(self, prompt: str) -> AsyncGenerator[str, None]:
    completion = await self._async_client.chat.completions.create(..., stream=True)
    async for chunk in completion:
        content = chunk.choices[0].delta.content
        if content:
            yield content
```

**理由**:
- SSE 需要逐 token 推送，`agenerate` 拼接完整字符串不满足需求
- `astream` 是 `agenerate` 的流式版本，职责清晰
- 符合 ISP：需要流式的场景用 `astream`，需要完整结果的用 `agenerate`

### D7: SSE 事件协议

```
event: progress       → { completed, total, failed }
event: phase_start    → { phase, doc_id?, batch_index?, query_index? }
event: llm_token      → { content }
event: llm_done       → { raw_length }
event: question_generated → { index, query, type, difficulty }
event: result         → { query, answer, chunk_ids, quality_score, status }
event: task_paused    → {}
event: task_resumed   → {}
event: task_done      → { completed, failed }
event: task_failed    → { error }
event: task_cancelled → {}
```

### D8: 重试失败项

**选择**: `POST /generation-tasks/{tid}/retry-failed` 重新处理失败的问题

实现方式：Runner 记录失败项的上下文（prompt、chunk 信息），重试时重新调用 LLM。

**理由**: 单条重试精准，不浪费 LLM 调用，用户体验好。

## Risks / Trade-offs

- **[SSE 连接数限制]** → 浏览器对同域 SSE 连接数有限制（Chrome 6个）。当前场景每个用户最多 1 个活跃任务，不构成问题。若未来需要多任务并行，需考虑连接复用。
- **[Runner 内存泄漏]** → 任务完成后必须从 TaskManager 移除 Runner，否则内存泄漏。在 `task_done`/`task_failed`/`task_cancelled` 事件后自动移除。
- **[暂停响应延迟]** → 暂停检查在每条问题处理完后，最坏延迟 = 1 次 LLM 调用时间（几秒到十几秒）。可接受。
- **[断线不补发历史事件]** → 用户断线重连后只能看到进度数字，看不到之前的流式内容。权衡简单性，可接受。
- **[服务重启丢失 Runner]** → Runner 是内存对象，服务重启后无法恢复暂停/继续控制。任务状态已持久化到 DB，重启后任务标记为 failed。
