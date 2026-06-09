## Why

检索平均耗时 20+ 秒，前端 axios 全局 timeout 仅 15s，导致检索请求必然超时报错。批量检索更是黑盒等待——前端 2 个一批串行请求，全部因超时失败，过一会刷新页面发现后端实际已完成检索。用户体验极差：等待时间长、无进度反馈、超时报错但实际成功。

此外，当前 `latency_ms` 只记录总耗时，无法区分瓶颈在嵌入 API 调用还是向量检索，不利于性能优化。`_load_chunk_map` 加载全量 100000 条 chunk 也造成不必要的性能浪费。

## What Changes

- 检索接口改为异步任务模式：`POST /retrieval` 立即返回 `task_id`，后台执行检索，前端轮询任务状态
- 新增批量检索接口 `POST /golden/batch-retrieval`，后台 2 个一批串行执行，返回任务列表
- 新增任务查询接口 `GET /golden/retrieval/tasks/{task_id}`，返回任务状态和结果
- `golden_retrieval` 表新增 `embed_latency_ms` 和 `search_latency_ms` 字段，拆分嵌入和检索耗时
- `RetrieverPort.retrieve()` 返回值改为 `RetrievalOutput`，携带分阶段耗时
- `ChunkRepositoryPort` 新增 `get_by_ids()` 方法，替代全量加载
- 前端检索交互改为轮询模式，批量检索展示进度条

## Capabilities

### New Capabilities
- `retrieval-async-task`: 异步任务模式检索，支持单条和批量，前端轮询获取结果
- `chunk-batch-query`: 按 ID 批量查询 chunk，替代全量加载

### Modified Capabilities
- `retrieval-latency-split`: 检索耗时拆分为嵌入耗时和向量检索耗时，持久化到 DB

## Impact

- **后端 API**: 新增 3 个端点（异步检索、批量检索、任务查询），修改 1 个端点（检索改为异步）
- **后端核心**: 新增 `RetrievalTaskManager` 内存任务管理器，`RetrieverPort` 返回类型变更，`GoldenRetrieveUseCase` 适配分阶段计时
- **数据库**: `golden_retrieval` 表新增 2 列（`embed_latency_ms`, `search_latency_ms`）
- **前端**: 检索交互从同步等待改为异步轮询，批量检索增加进度展示
- **依赖**: 无新外部依赖（使用 `asyncio.create_task` + 内存字典）
