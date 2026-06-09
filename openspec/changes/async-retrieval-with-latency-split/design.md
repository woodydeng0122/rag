## Context

当前检索流程是同步阻塞模式：前端 `POST /golden/{id}/retrieval` 发起请求，后端执行完整检索（嵌入 API ~15s + 向量检索 ~3s + 加载 chunk + 持久化）后才返回响应。前端 axios 全局 timeout=15s，必然超时。

批量检索在前端以 2 个一批串行调用 `createRetrieval`，所有请求均因超时失败。但后端实际完成了检索并持久化结果，刷新页面后 `GET /golden/{id}/retrieval` 可正常获取。

`CosineRetriever.retrieve()` 内部将"嵌入查询"和"向量检索"混在一起，无法区分耗时瓶颈。`_load_chunk_map` 通过 `list_by_project(limit=100000)` 加载全量 chunk 再内存过滤，效率低。

项目中已有 `TaskManager` 模式（用于黄金数据集生成任务），可复用相同架构。

## Goals / Non-Goals

**Goals:**
- 检索接口改为异步任务模式，前端不再因超时报错
- 批量检索支持进度反馈（"3/10 已完成"）
- 检索耗时拆分为 `embed_latency_ms` 和 `search_latency_ms`，持久化到 DB
- `_load_chunk_map` 改为按 ID 批量查询，提升性能
- 保持现有 `GET /golden/{id}/retrieval` 接口不变，刷新页面仍可获取结果
- 批量检索并发度保持 2，不增加后端压力

**Non-Goals:**
- 不做 SSE/WebSocket 实时推送（轮询足够）
- 不做检索任务暂停/取消（检索是短任务，20s 内完成）
- 不做检索结果缓存/去重
- 不做嵌入 API 本身的性能优化（那是外部服务）
- 不增加批量检索并发度

## Decisions

### D1: 异步任务 + 轮询，而非 SSE

**选择**: `POST` 返回 `task_id`，前端轮询 `GET /tasks/{task_id}`

**理由**:
- 检索是短任务（20s），轮询 2-3 次即可完成，SSE 过重
- 轮询实现简单，前端 `setInterval` + `clearInterval` 即可
- 与项目已有的 `TaskManager` 模式一致
- SSE 需要处理连接管理、断线重连，复杂度高

**替代方案**: SSE 实时推送 — 检索任务短，轮询延迟可忽略，不值得引入 SSE 复杂度

### D2: 内存任务管理器

**选择**: `RetrievalTaskManager` 使用内存字典管理任务状态

```python
class RetrievalTaskManager:
    _tasks: dict[str, RetrievalTask]  # task_id → task

class RetrievalTask:
    id: str
    golden_id: str
    status: str  # pending / running / completed / failed
    result: GoldenRetrievalResult | None
    error: str | None
```

**理由**:
- 检索结果已持久化到 DB，任务状态只是临时过渡
- 服务重启后通过 `GET /golden/{id}/retrieval` 仍可获取结果
- 无需引入 Redis/Celery，复杂度最低
- 与项目中 `TaskManager`（生成任务）模式一致

**风险**: 服务重启丢失进行中的任务状态 → 可接受，用户刷新页面后通过 GET 接口获取已完成的结果

### D3: RetrieverPort 返回类型变更

**选择**: `retrieve()` 返回 `RetrievalOutput` 而非 `list[RetrievalResult]`

```python
@dataclass
class RetrievalOutput:
    results: list[RetrievalResult]
    embed_latency_ms: int
    search_latency_ms: int
```

**理由**:
- 耗时统计应在基础设施层（CosineRetriever）完成，而非应用层
- CosineRetriever 是唯一知道嵌入和检索分界点的组件
- 应用层只需读取分阶段耗时，不需要自己计时

**影响**: `RetrieveUseCase` 和 `AskUseCase` 需适配新返回类型

### D4: 批量检索保持 2 并发

**选择**: 批量检索在 `RetrievalTaskManager` 中用 `asyncio.Semaphore(2)` 控制并发

**理由**:
- 后端无法承受 10 个并行检索
- 保持与当前前端 2 个一批串行行为一致
- Semaphore 在后台协程中控制，不阻塞 API 响应

### D5: chunk 按需查询

**选择**: `ChunkRepositoryPort` 新增 `get_by_ids(chunk_ids)` 方法

```python
async def get_by_ids(self, chunk_ids: list[str]) -> list[Chunk]:
```

**理由**:
- 当前 `_load_chunk_map` 加载全量 100000 条 chunk，实际只需 10 条
- SQL `WHERE id = ANY($1)` 精准查询，性能提升显著
- 不影响现有 `list_by_project` 接口

### D6: 前端轮询策略

**选择**: 轮询间隔 2s，最大等待 5 分钟

**理由**:
- 检索平均 20s，2s 轮询最多 10 次即可完成
- 5 分钟上限覆盖极端情况（批量检索）
- 轮询在组件 unmount 时自动清理

### D7: API 接口设计

**选择**: RESTful 风格

```
POST   /api/projects/{pid}/golden/{id}/retrieval       → 异步触发检索，返回 { task_id, status }
GET    /api/projects/{pid}/golden/retrieval/tasks/{tid} → 查询任务状态和结果
POST   /api/projects/{pid}/golden/batch-retrieval       → 批量检索，返回任务列表
GET    /api/projects/{pid}/golden/{id}/retrieval        → 保持不变，刷新获取结果
```

**理由**:
- `POST /retrieval` 触发操作返回任务标识，符合 REST 语义
- `GET /tasks/{tid}` 查询任务状态，资源化任务
- `POST /batch-retrieval` 批量操作，与现有 `batch-approve`/`batch-reject` 风格一致
- 保持 `GET /retrieval` 不变，向下兼容

## Risks / Trade-offs

- **[任务状态丢失]** → 服务重启后内存中的任务状态丢失，进行中的检索结果无法通过 task_id 查询。但检索结果已持久化到 DB，用户刷新页面后可通过 `GET /golden/{id}/retrieval` 获取。可接受。
- **[RetrieverPort 接口变更]** → `retrieve()` 返回类型变更影响 `RetrieveUseCase` 和 `AskUseCase`。改动量小，两处适配即可。
- **[轮询开销]** → 每次轮询是一次 HTTP 请求，但检索场景并发低（单用户操作），2s 间隔对后端无压力。
- **[批量检索串行]** → 保持 2 并发意味着 10 条检索需 ~100s。但这是后端能力限制，异步模式下用户至少能看到进度，比黑盒等待体验好。
