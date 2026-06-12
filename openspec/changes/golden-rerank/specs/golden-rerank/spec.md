## ADDED Requirements

### Requirement: 触发重排

系统 SHALL 允许对已有粗排结果的黄金记录执行 cross-encoder 重排。

- **前置条件**: 黄金记录存在，且该记录已有粗排结果（golden_retrieval 记录）
- **输入**: record_id, top_k (默认 10, 范围 1-100)
- **约束**: top_k MUST ≤ 粗排的 max_k，否则返回 400 错误
- **处理**:
  1. 加载黄金记录，获取 query 和 ground_truth_chunks
  2. 加载粗排结果及明细（GoldenRetrieval + GoldenRetrievalItem）
  3. 取粗排前 top_k 个候选（按 rank 升序）
  4. 批量加载候选 chunk 的 content
  5. 调用 RerankerPort.rerank(query, [chunk.content...], top_k)
  6. 计时开始（rerank 调用前）到计时结束（rerank 返回后），计算 latency_ms
  7. 按 rerank_score 降序排列，分配 rerank_rank（从 1 开始）
  8. 删除该 golden_id 的旧重排结果（覆盖模式）
  9. 写入 golden_rerank 记录（top_k, latency_ms, model_name）
  10. 写入 golden_rerank_item 列表（chunk_id, original_rank, rerank_score, rerank_rank）
- **输出**: 完整重排结果（含 items、指标、GT 命中标记）
- **异常**: 记录不存在 → 404；无粗排结果 → 400；top_k > 粗排 max_k → 400

#### Scenario: 成功重排
- **WHEN** 对已有粗排结果（max_k=50）的黄金记录执行重排，top_k=10
- **THEN** 系统取粗排前 10 个候选，执行 cross-encoder 重排，返回重排后的 10 个结果，按 rerank_score 降序排列

#### Scenario: 无粗排结果时重排
- **WHEN** 对没有粗排结果的黄金记录执行重排
- **THEN** 系统返回 400 错误，提示"该记录无粗排结果，请先执行检索"

#### Scenario: top_k 超过粗排 max_k
- **WHEN** 粗排 max_k=10，用户请求 top_k=20
- **THEN** 系统返回 400 错误，提示"top_k 不能超过粗排 max_k (10)"

### Requirement: 获取重排结果

系统 SHALL 允许查询黄金记录的重排结果。

- **前置条件**: 黄金记录存在
- **处理**:
  1. 查询 golden_rerank by golden_id
  2. 查询 golden_rerank_item by rerank_id
  3. 批量加载 chunk 内容（chunk_id → content, heading, source_file, file_type）
  4. 计算 is_ground_truth：chunk_id ∈ ground_truth_chunks → true
- **输出**: 重排结果（含 chunk 内容、GT 命中标记、original_rank、rerank_score、rerank_rank）
- **异常**: 无重排结果 → 404；记录不存在 → 404

#### Scenario: 获取已有重排结果
- **WHEN** 查询已有重排结果的黄金记录
- **THEN** 返回重排结果列表，每项包含 chunk_id、content、original_rank、rerank_score、rerank_rank、is_ground_truth

#### Scenario: 无重排结果
- **WHEN** 查询没有重排结果的黄金记录
- **THEN** 返回 404 错误

### Requirement: 重排结果持久化

系统 SHALL 将重排结果独立存储，与粗排结果分离。

- **数据约束**:
  - golden_rerank.golden_id 是 UNIQUE 的（1:1 覆盖模式）
  - golden_rerank_item.rerank_rank 从 1 开始，按 rerank_score 降序
  - 删除 golden 记录时 CASCADE 删除关联的 rerank 和 rerank_items
  - top_k 范围 1-100

#### Scenario: 覆盖旧重排结果
- **WHEN** 对同一黄金记录再次执行重排
- **THEN** 旧的重排结果及明细被删除，写入新的重排结果

#### Scenario: 删除黄金记录级联删除
- **WHEN** 删除一条有重排结果的黄金记录
- **THEN** 关联的 golden_rerank 和 golden_rerank_item 全部被删除

### Requirement: 重排 API

系统 SHALL 提供以下 RESTful API 端点：

- `POST /api/projects/{project_id}/golden/{record_id}/rerank` — 触发重排
  - 请求体: `{ top_k: int }`
  - 响应: RerankResponse
- `GET /api/projects/{project_id}/golden/{record_id}/rerank` — 获取重排结果
  - 响应: RerankResponse

#### Scenario: 触发重排 API 调用
- **WHEN** POST /api/projects/{id}/golden/{record_id}/rerank，body={top_k: 10}
- **THEN** 返回 200 及 RerankResponse，包含重排结果和指标

#### Scenario: 获取重排结果 API 调用
- **WHEN** GET /api/projects/{id}/golden/{record_id}/rerank
- **THEN** 返回 200 及 RerankResponse

### Requirement: 黄金记录列表扩展重排摘要

系统 SHALL 在黄金记录列表响应中包含重排摘要信息。

- GoldenResponse 新增 `has_rerank` 布尔字段
- GoldenResponse 新增 `rerank_summary` 字段（结构同 RetrievalSummary：hit_count, gt_total, hit_ranks）
- 后端查询时批量获取重排命中摘要

#### Scenario: 列表包含重排摘要
- **WHEN** 获取黄金记录列表
- **THEN** 每条记录包含 has_rerank 和 rerank_summary 字段

### Requirement: RerankerPort 端口

系统 SHALL 定义 RerankerPort 抽象端口，供基础设施层实现。

- 端口方法: `async def rerank(self, query: str, documents: list[str], top_k: int) -> list[RerankResult]`
- RerankResult 包含: index (原始文档索引), score (cross-encoder 分数)

#### Scenario: RerankerPort 实现
- **WHEN** 调用 RerankerPort.rerank(query, documents, top_k)
- **THEN** 返回 top_k 个 RerankResult，按 score 降序排列

### Requirement: SentenceTransformerReranker 适配器

系统 SHALL 提供 SentenceTransformerReranker 适配器，基于 sentence-transformers 的 CrossEncoder 类加载本地 bge-reranker-base 模型。

- 模型路径: models/BAAI/bge-reranker-base
- 单例模式，启动时加载
- 实现 RerankerPort 接口

#### Scenario: 本地模型重排
- **WHEN** 调用 SentenceTransformerReranker.rerank(query, [doc1, doc2, doc3], top_k=2)
- **THEN** 使用 CrossEncoder 对 (query, doc) 对打分，返回分数最高的 2 个结果
