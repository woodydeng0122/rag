## 1. 领域层 — 端口与实体

- [x] 1.1 新增 `RerankerPort` 端口（`domain/ports/reranker.py`）：定义 `rerank(query, documents, top_k) -> list[RerankResult]` 抽象方法
- [x] 1.2 新增 `RerankResult` 值对象（`domain/value_objects/rerank_result.py`）：index (int), score (float)
- [x] 1.3 新增 `GoldenRerank` 实体（`domain/entities/golden_rerank.py`）：golden_id, top_k, latency_ms, model_name, created_at
- [x] 1.4 新增 `GoldenRerankItem` 实体（`domain/entities/golden_rerank_item.py`）：rerank_id, chunk_id, original_rank, rerank_score, rerank_rank
- [x] 1.5 新增 `GoldenRerankRepositoryPort` 端口（`domain/ports/golden_rerank_repository.py`）：save, get_by_golden_id, delete_by_golden_id, exists_by_golden_ids, get_rerank_summaries

## 2. 基础设施层 — Reranker 适配器

- [x] 2.1 新增 `SentenceTransformerReranker`（`infra/reranker/sentence_transformer_reranker.py`）：实现 RerankerPort，使用 CrossEncoder 加载 `models/BAAI/bge-reranker-base`

## 3. 基础设施层 — 数据库仓储

- [x] 3.1 新增数据库迁移：创建 `golden_rerank` 和 `golden_rerank_item` 表，golden_rerank.golden_id UNIQUE，golden_rerank_item.rerank_id CASCADE
- [x] 3.2 新增 `PgGoldenRerankRepository`（`infra/repositories/pg_golden_rerank_repository.py`）：实现 GoldenRerankRepositoryPort 的所有方法
- [x] 3.3 修改 `PgGoldenRepository` 的删除逻辑：删除 golden 记录时 CASCADE 删除 golden_rerank 和 golden_rerank_item

## 4. 应用层 — 重排用例

- [x] 4.1 新增 `GoldenRerankUseCase`（`application/usecases/golden_rerank.py`）：
  - `execute(record_id, top_k)` — 读取粗排结果 → 取前 top_k 候选 → 调用 reranker → 保存重排结果 → 返回含 GT 命中的完整结果
  - `get_rerank(record_id)` — 获取重排结果
  - `get_rerank_summaries(golden_ids)` — 批量获取重排命中摘要
  - `has_rerank_for_records(golden_ids)` — 批量判断是否有重排结果

## 5. 适配器层 — API 路由与 Schema

- [x] 5.1 新增 Pydantic schema（`adapters/api/schemas/golden.py`）：CreateRerankRequest, RerankItemResponse, RerankResponse
- [x] 5.2 修改 `GoldenResponse`：新增 has_rerank (bool) 和 rerank_summary (RerankSummaryResponse | None) 字段
- [x] 5.3 修改 `GoldenPresenter.to_response`：接受 has_rerank 和 rerank_summary 参数
- [x] 5.4 新增 API 路由（`adapters/api/routes/golden.py`）：
  - `POST /golden/{record_id}/rerank` — 触发重排
  - `GET /golden/{record_id}/rerank` — 获取重排结果
- [x] 5.5 修改 `list_goldens` 路由：并行查询重排摘要，传入 GoldenPresenter

## 6. 组装 — Container 注入

- [x] 6.1 修改 `Container`：新增 golden_rerank_usecase 字段
- [x] 6.2 修改 `_build_infra`：创建 SentenceTransformerReranker 单例、PgGoldenRerankRepository
- [x] 6.3 修改 `_build_usecases`：组装 GoldenRerankUseCase

## 7. 前端 — API 与模型

- [x] 7.1 新增前端模型（`api/model/goldenModel.ts`）：RerankItem, RerankResponse, CreateRerankParams, RerankSummary；扩展 GoldenItem 增加 has_rerank 和 rerank_summary
- [x] 7.2 新增前端 API（`api/golden.ts`）：createRerank, getRerank

## 8. 前端 — 黄金数据集页面

- [x] 8.1 表格新增"重排"列：无粗排显示 `--`，有粗排无重排显示蓝色「重排」按钮，有重排显示命中 tag
- [x] 8.2 工具栏新增"批量重排"按钮 + 弹窗（输入 top_k），前置校验选中记录都有粗排结果
- [x] 8.3 新增重排 Drawer：与粗排 Drawer 类似，展示重排结果列表和指标（模型名、总耗时、top_k、recall@k）
- [x] 8.4 实现批量重排逻辑：调用 createRerank API，更新列表中的重排摘要
