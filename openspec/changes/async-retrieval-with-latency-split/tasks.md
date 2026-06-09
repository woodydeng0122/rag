## 1. 数据库迁移

- [ ] 1.1 新建 `009_split_retrieval_latency.sql`，为 `golden_retrieval` 表新增 `embed_latency_ms` 和 `search_latency_ms` 列

## 2. 领域层变更

- [ ] 2.1 `GoldenRetrieval` 实体新增 `embed_latency_ms: int = 0` 和 `search_latency_ms: int = 0` 字段
- [ ] 2.2 新增 `RetrievalOutput` 值对象，包含 `results`、`embed_latency_ms`、`search_latency_ms`
- [ ] 2.3 `RetrieverPort.retrieve()` 返回类型从 `list[RetrievalResult]` 改为 `RetrievalOutput`
- [ ] 2.4 `ChunkRepositoryPort` 新增 `get_by_ids(chunk_ids: list[str]) -> list[Chunk]` 抽象方法

## 3. 基础设施层变更

- [ ] 3.1 `CosineRetriever.retrieve()` 分阶段计时，返回 `RetrievalOutput`
- [ ] 3.2 `PgGoldenRetrievalRepository` SQL 适配新字段（save/get_by_golden_id 读写 `embed_latency_ms`、`search_latency_ms`）
- [ ] 3.3 `PgChunkRepository` 实现 `get_by_ids()` 方法，SQL `WHERE id = ANY($1::varchar[])`

## 4. 应用层变更

- [ ] 4.1 `GoldenRetrieveUseCase.execute()` 适配 `RetrievalOutput`，将分阶段耗时传入 `GoldenRetrieval` 实体
- [ ] 4.2 `GoldenRetrieveUseCase._load_chunk_map()` 改用 `chunk_repo.get_by_ids()` 替代全量加载
- [ ] 4.3 `RetrieveUseCase.execute()` 适配 `RetrievalOutput` 返回类型
- [ ] 4.4 `AskUseCase` 适配 `RetrieverPort` 新返回类型（从 `RetrievalOutput.results` 取结果）
- [ ] 4.5 新建 `RetrievalTaskManager`，管理检索任务状态（内存字典 + asyncio.Semaphore(2)）
- [ ] 4.6 `RetrievalTaskManager` 实现 `create_task()`、`create_batch_tasks()`、`get_task()` 方法
- [ ] 4.7 `RetrievalTaskManager._run_task()` 后台协程执行检索，更新任务状态

## 5. API 层变更

- [ ] 5.1 `RetrievalResponse` Schema 新增 `embed_latency_ms`、`search_latency_ms` 字段
- [ ] 5.2 新增 `RetrievalTaskResponse` Schema（task_id, golden_id, status, result, error）
- [ ] 5.3 新增 `BatchRetrievalRequest` Schema（record_ids, max_k）
- [ ] 5.4 新增 `BatchRetrievalTaskResponse` Schema（tasks: list[RetrievalTaskResponse]）
- [ ] 5.5 修改 `POST /golden/{id}/retrieval` 路由：改为异步任务模式，立即返回 task 信息
- [ ] 5.6 新增 `GET /golden/retrieval/tasks/{task_id}` 路由：查询任务状态和结果
- [ ] 5.7 新增 `POST /golden/batch-retrieval` 路由：批量触发检索
- [ ] 5.8 `_retrieval_result_to_response()` 适配新字段
- [ ] 5.9 `bootstrap/container.py` 注册 `RetrievalTaskManager` 单例

## 6. 前端变更

- [ ] 6.1 `request.ts`：检索相关请求 timeout 改为 30s（POST /retrieval、GET /tasks/{id}、POST /batch-retrieval）
- [ ] 6.2 `goldenModel.ts`：新增 `RetrievalTaskResponse`、`BatchRetrievalTaskResponse` 类型
- [ ] 6.3 `golden.ts` API：新增 `createRetrievalAsync`、`getRetrievalTask`、`batchRetrieve` 接口
- [ ] 6.4 `Golden.vue` 单条检索：改为异步轮询模式（POST → 轮询 GET task → 展示结果）
- [ ] 6.5 `Golden.vue` 批量检索：改为异步任务模式，展示进度条 "3/10 已完成"
- [ ] 6.6 `Golden.vue` 检索结果展示：新增嵌入耗时和检索耗时 Tag
