## 1. 数据库 Migration

- [x] 1.1 创建 migration 008: 新增 golden_retrieval 表（id, golden_id UNIQUE FK→golden, max_k, latency_ms, embed_model_name, created_at）和 golden_retrieval_item 表（id, retrieval_id FK→golden_retrieval, chunk_id, score, rank），加索引 idx_golden_retrieval_golden_id、idx_golden_retrieval_item_retrieval_id

## 2. Domain 层

- [x] 2.1 新增实体 `GoldenRetrieval`：id, golden_id, max_k, latency_ms, embed_model_name, created_at
- [x] 2.2 新增实体 `GoldenRetrievalItem`：id, retrieval_id, chunk_id, score, rank
- [x] 2.3 新增端口 `GoldenRetrievalRepositoryPort`：save（含 items）、get_by_golden_id、delete_by_golden_id、exists_by_golden_id、exists_by_golden_ids

## 3. Infra 层

- [x] 3.1 实现 `PgGoldenRetrievalRepository`：save（写入 retrieval + items）、get_by_golden_id（join items）、delete_by_golden_id（CASCADE 删 items）、exists_by_golden_id、exists_by_golden_ids

## 4. Application 层

- [x] 4.1 新增 `GoldenRetrieveUseCase`：依赖 RetrieverPort、GoldenRepositoryPort、GoldenRetrievalRepositoryPort、ChunkRepositoryPort、ProjectRepositoryPort、EmbedModelRepositoryPort
  - `execute(record_id, max_k)` → 加载记录 → 检索 → 计时 → 获取模型名 → 删旧 → 写新 → 返回结果
  - `get_retrieval(record_id)` → 加载记录 → 查 retrieval → join chunk 内容 → 计算 GT 命中 → 返回
  - `has_retrieval_for_records(golden_ids)` → 批量查询哪些记录有检索结果
- [x] 4.2 更新 Container：注册 GoldenRetrieveUseCase 及新依赖

## 5. API 层

- [x] 5.1 新增 schemas：`CreateRetrievalRequest(max_k)`, `RetrievalItemResponse(chunk_id, score, rank, content, heading, source_file, is_ground_truth)`, `RetrievalResponse(id, golden_id, max_k, latency_ms, embed_model_name, created_at, items)`
- [x] 5.2 golden 路由新增 `POST /golden/{record_id}/retrieval` 端点
- [x] 5.3 golden 路由新增 `GET /golden/{record_id}/retrieval` 端点
- [x] 5.4 更新 `GoldenResponse`：新增 `has_retrieval` 字段
- [x] 5.5 更新 `GoldenPresenter.to_response`：新增 has_retrieval 参数
- [x] 5.6 更新 golden list API：通过 has_retrieval_for_records 批量查询 has_retrieval

## 6. 前端 API 层

- [x] 6.1 更新 `api/model/goldenModel.ts`：GoldenItem 新增 has_retrieval 字段；新增 RetrievalItem、RetrievalResponse、CreateRetrievalParams 类型
- [x] 6.2 更新 `api/golden.ts`：新增 `createRetrieval(projectId, recordId, { max_k })` 和 `getRetrieval(projectId, recordId)` 方法

## 7. 前端页面

- [x] 7.1 Golden.vue 表格 columns 新增「检索」列（位于「创建时间」和「操作」之间）
- [x] 7.2 实现「检索」列渲染：has_retrieval ? 绿色「查看结果」按钮 : 蓝色「检索」按钮
- [x] 7.3 实现检索 Modal：query 只读展示、max_k 输入框（默认 10）、确认检索按钮
- [x] 7.4 实现检索结果展示：items 列表（rank、score、GT 标记、chunk 内容）、指标栏（模型、耗时、max_k、GT 命中数）、重新检索按钮
- [x] 7.5 点击「查看结果」按钮时调用 GET retrieval API 并在 Modal 中展示
