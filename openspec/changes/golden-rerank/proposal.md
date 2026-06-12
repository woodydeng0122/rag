## Why

当前黄金数据集只有粗排（向量/BM25/Hybrid 检索），无法评估重排（rerank）对检索质量的提升效果。需要添加基于 cross-encoder 的重排能力，让用户能对比粗排与重排的 recall@k 差异，量化 reranker 的实际价值。

## What Changes

- 新增本地 cross-encoder reranker 适配器（基于 `models/BAAI/bge-reranker-base`），实现 `RerankerPort` 端口
- 新增 `golden_rerank` + `golden_rerank_item` 数据表，独立存储重排结果（与粗排分离）
- 新增重排用例 `GoldenRerankUseCase`：从粗排结果中取前 top_k 个候选，经 cross-encoder 重排后持久化
- 新增 RESTful API：`POST/GET /projects/{id}/golden/{record_id}/rerank`
- 前端黄金数据集表格新增"重排"列，展示重排命中摘要
- 前端新增"批量重排"按钮 + 弹窗（输入 top_k），批量执行重排
- 前端新增重排 Drawer（与粗排 Drawer 类似），展示重排结果和指标
- 重排指标：总耗时、recall@k，与粗排指标区分展示

## Capabilities

### New Capabilities
- `golden-rerank`: 黄金记录重排功能 — 基于粗排结果执行 cross-encoder 重排、持久化重排结果和指标、展示重排命中情况与 recall@k

### Modified Capabilities
- `golden-retrieval`: 黄金记录列表需扩展 `has_rerank` 和 `rerank_summary` 字段，前端表格新增重排列

## Impact

- **后端新增**: RerankerPort 端口、SentenceTransformerReranker 适配器、GoldenRerankUseCase、GoldenRerank/GoldenRerankItem 实体、PG 仓储、API 路由、Pydantic schema
- **后端修改**: GoldenPresenter（扩展 rerank 字段）、Container（注入 reranker 和 usecase）、数据库迁移（新表）
- **前端新增**: 重排 API 调用、重排模型类型、批量重排弹窗、重排 Drawer
- **前端修改**: Golden.vue 表格新增重排列、工具栏新增批量重排按钮、列表数据扩展 rerank 字段
- **依赖**: sentence-transformers 库（已有）、模型文件 `models/BAAI/bge-reranker-base`（已有）
