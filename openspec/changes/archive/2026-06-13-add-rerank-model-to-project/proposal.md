## Why

当前项目的重排模型（reranker）是全局硬编码的 `BAAI/bge-reranker-base`，无法按项目区分配置。粗排嵌入模型已通过 `embed_model_id` 实现了项目级配置，但重排模型缺少对应机制，导致：不同项目无法使用不同的重排模型；无法跳过重排（项目不配置重排模型时应直接使用粗排结果）；重排模型无法通过注册表统一管理。

## What Changes

- `embed_model` 表新增 `model_type` 列（`"embed"` | `"reranker"`），区分嵌入模型和重排模型
- `project` 表新增 `rerank_model_id` FK 列（可选，指向 `embed_model` 表中 `model_type="reranker"` 的行）
- `ModelScanner` 扫描时通过 `modules.json` 是否存在自动判定 `model_type`
- 新增 `RerankerPool`，按 `model_path` 缓存 `CrossEncoder` 实例，与 `EmbedderPool` 对称
- `GoldenRerankUseCase` 从项目配置获取重排模型，通过 `RerankerPool` 获取实例
- `rerank_model_id = NULL` 时，拒绝触发重排和重排评估，问答/检索流程不受影响

## Capabilities

### New Capabilities
- `rerank-model-config`: 重排模型的项目级配置能力 — 包括模型注册表扩展（model_type）、项目表 FK、扫描器自动识别、RerankerPool、用例适配

### Modified Capabilities
- `project-management`: 项目创建/响应需包含 rerank_model_id 和 rerank_model_name
- `project-evaluation-stats`: 重排评估需校验项目是否配置了重排模型

## Impact

- **数据库**: `embed_model` 表加 `model_type` 列（已有行设为 `"embed"`）；`project` 表加 `rerank_model_id` 列（FK，默认 NULL）
- **Domain 层**: `EmbedModel` 实体加 `model_type` 字段；`Project` 实体加 `rerank_model_id` 字段；`ScannedModel` VO 加 `model_type`
- **Infra 层**: `ModelScanner` 自动识别模型类型；新增 `RerankerPool`；`PgProjectRepository` / `PgEmbedModelRepository` SQL 适配
- **Application 层**: `GoldenRerankUseCase` 从项目获取重排模型；`ScanEmbedModelsUseCase` 写入 `model_type`
- **API 层**: `CreateProjectRequest` / `ProjectResponse` 加重排模型字段
- **前端**: 项目表单加重排模型选择（可选）
