## 1. 数据库迁移

- [x] 1.1 新建迁移文件 `022_rerank_model_type.sql`：`embed_model` 表加 `model_type VARCHAR(32) NOT NULL DEFAULT 'embed'` 列；`UPDATE embed_model SET model_type = 'embed' WHERE model_type IS NULL`
- [x] 1.2 迁移文件中 `project` 表加 `rerank_model_id UUID REFERENCES embed_model(id) DEFAULT NULL` 列
- [x] 1.3 迁移文件中新增索引 `idx_project_rerank_model_id ON project(rerank_model_id)`

## 2. Domain 层 — 实体与值对象

- [x] 2.1 `EmbedModel` 实体加 `model_type: str = "embed"` 字段；`ensure_complete()` 按 `model_type` 差异化校验（reranker 跳过 dimension 校验）；`reconstruct()` 方法加 `model_type` 参数
- [x] 2.2 `Project` 实体加 `rerank_model_id: str = ""` 字段
- [x] 2.3 `ScannedModel` 值对象加 `model_type: str = "embed"` 字段
- [x] 2.4 `ModelScannerPort` 接口无需改动（`scan()` 返回 `ScannedModel` 已含 `model_type`）

## 3. Infra 层 — 扫描器与仓储

- [x] 3.1 `ModelScanner.scan()` 通过 `modules.json` 是否存在判定 `model_type`；reranker 的 `dimension` 设为 0
- [x] 3.2 `PgEmbedModelRepository` SQL 适配 `model_type` 列：`_SELECT`、INSERT、UPDATE、`_row_to_embed_model` 均包含 `model_type`
- [x] 3.3 `PgProjectRepository` SQL 适配 `rerank_model_id` 列：`_SELECT`、INSERT、UPDATE、`_row_to_project` 均包含 `rerank_model_id`

## 4. Infra 层 — RerankerPool

- [x] 4.1 新建 `src/rag/infra/reranker/reranker_pool.py`，实现 `RerankerPool`：按 `model_path` 缓存 `CrossEncoder` 实例，支持 `get(model_path)` 方法，LRU 淘汰，`max_size` 限制
- [x] 4.2 `SentenceTransformerReranker` 改为接受 `model_path` 参数（不再硬编码），构造函数签名改为 `__init__(self, model_path: str)`

## 5. Application 层 — 用例适配

- [x] 5.1 `ScanEmbedModelsUseCase` 适配 `model_type`：扫描结果按 `model_type` 写入 `embed_model` 表；注册 reranker 时 `dimension=0`
- [x] 5.2 `GoldenRerankUseCase` 适配：新增依赖 `project_repo`、`embed_model_repo`、`reranker_pool`；`execute()` 前置校验 `project.rerank_model_id`；从 `embed_model` 获取模型路径；通过 `RerankerPool.get(model_path)` 获取实例；`model_name` 从 `embed_model.name` 获取
- [x] 5.3 `ProjectEvaluationUseCase._execute_rerank_eval()` 前置校验 `project.rerank_model_id` 是否为空
- [x] 5.4 `ProjectUseCase` 适配：创建项目时校验 `rerank_model_id` 对应的 `embed_model.model_type` 为 `"reranker"`；查询项目时关联查询 `rerank_model_name`

## 6. API 层 — Schema 与路由

- [x] 6.1 `CreateProjectRequest` 加 `rerank_model_id: str | None = None` 字段
- [x] 6.2 `ProjectResponse` 加 `rerank_model_id: str = ""` 和 `rerank_model_name: str = ""` 字段
- [x] 6.3 项目路由中创建/查询接口适配新字段

## 7. 组装 — Container

- [x] 7.1 `container.py` 中 `SentenceTransformerReranker()` 改为不再全局实例化；新增 `RerankerPool` 实例化并注入
- [x] 7.2 `GoldenRerankUseCase` 构造参数更新：注入 `project_repo`、`embed_model_repo`、`reranker_pool`
- [x] 7.3 `ProjectEvaluationUseCase` 构造参数更新：注入 `project_repo`

## 8. 前端适配 — 项目页

- [x] 8.1 `embedModelModel.ts`：`EmbedModelItem` 接口加 `model_type: "embed" | "reranker"` 字段
- [x] 8.2 `projectModel.ts`：`CreateProjectParams` 加 `rerank_model_id?: string`；`ProjectItem` 加 `rerank_model_id: string` + `rerank_model_name: string`
- [x] 8.3 `embedModel.ts` Store：新增 `onlineEmbedModels` 和 `onlineRerankerModels` 计算属性
- [x] 8.4 `ProjectList.vue`：项目创建表单加重排模型选择下拉框（可选，数据源 `onlineRerankerModels`）；嵌入模型数据源改为 `onlineEmbedModels`；卡片展示 `rerank_model_name`；defaultForm 加 `rerank_model_id`

## 9. 前端适配 — 模型配置页

- [x] 9.1 `EmbedModelConfig.vue` 表格新增"类型"列：在"维度"列之前，`model_type="embed"` 显示蓝色"嵌入"标签，`model_type="reranker"` 显示绿色"重排"标签
- [x] 9.2 `EmbedModelConfig.vue` "维度"列差异化：reranker 类型显示 "-"，embed 类型正常显示数值
- [x] 9.3 `EmbedModelConfig.vue` 详情 Drawer 新增"模型类型"项：显示中文标签（嵌入/重排）
