## 1. 数据库迁移

- [x] 1.1 创建迁移脚本 `002_embed_model.sql`：新增 `embed_model` 表（id, name, dimension, description, status, created_at, updated_at）
- [x] 1.2 迁移脚本：`project` 表新增 `embed_model_id` (UUID REFERENCES embed_model(id)) 和 `embed_dimension` (INT DEFAULT 512) 字段
- [x] 1.3 迁移脚本：`document` 表删除 `embedder_model` 字段
- [x] 1.4 迁移脚本：`embedding` 表向量列从 `VECTOR(512)` 改为 `VECTOR`（不指定维度），重建向量索引

## 2. Domain 层

- [x] 2.1 新增 `EmbedModel` 实体（id, name, dimension, description, status, created_at, updated_at）
- [x] 2.2 新增 `EmbedModelRepositoryPort` 端口（save, get_all, get_by_id, get_by_name, update_status）
- [x] 2.3 修改 `Project` 实体，新增 embed_model_id 和 embed_dimension 字段
- [x] 2.4 修改 `Document` 实体，删除 embedder_model 字段
- [x] 2.5 修改 `EmbedderPort`，支持按模型名获取 embedder 实例

## 3. Infra 层 — 模型扫描与仓储

- [x] 3.1 实现 `PgEmbedModelRepository`（save, get_all, get_by_id, get_by_name, update_status, save_batch）
- [x] 3.2 实现 `ModelScanner` 服务：扫描 `models/` 目录，解析 `config.json` 获取 name 和 dimension，返回模型信息列表
- [x] 3.3 实现 `EmbedderPool`：维护 `dict[str, SentenceTransformerEmbedder]` 缓存池，按模型名获取或创建实例，LRU 淘汰上限 3 个

## 4. Application 层 — 用例

- [x] 4.1 新增 `ScanEmbedModelsUseCase`：扫描 models/ 目录，upsert embed_model 表，更新 status
- [x] 4.2 修改 `ProcessDocumentUseCase`：从项目读取 embed_model_id，通过 EmbedderPool 获取对应 embedder 实例
- [x] 4.3 修改 `UploadUseCase`：移除 embedder_model 参数，不再写入 document 记录

## 5. API 层

- [x] 5.1 新增 `GET /api/embed-models` 端点，返回模型列表
- [x] 5.2 新增 `POST /api/embed-models/check-status` 端点，触发扫描并更新状态
- [x] 5.3 新增 embed_model schemas（EmbedModelItem, EmbedModelListResponse）
- [x] 5.4 修改 `POST /api/projects` 端点，新增 embed_model_id 必填参数，校验模型 online
- [x] 5.5 修改 `GET /api/projects` 和 `GET /api/projects/{id}` 返回，包含 embed_model_name 和 embed_dimension
- [x] 5.6 修改 `POST /api/projects/{project_id}/documents` 端点，移除 embedder_model Form 参数
- [x] 5.7 修改 project schemas，新增 embed_model_id 字段，移除 upload schemas 中的 embedder_model

## 6. Bootstrap 层

- [x] 6.1 修改 `Container`，新增 embed_model_repo、model_scanner、embedder_pool、scan_embed_models_usecase
- [x] 6.2 修改 `build_container`，启动时自动执行 ScanEmbedModelsUseCase
- [x] 6.3 修改 `Settings`，移除 embedder_model 配置项（模型从数据库读取）

## 7. 前端 — 模型配置页

- [x] 7.1 新增 `api/embedModel.ts`，封装 GET /api/embed-models 和 POST /api/embed-models/check-status
- [x] 7.2 新增 `api/model/embedModelModel.ts`，定义 EmbedModelItem 类型
- [x] 7.3 新增 `views/EmbedModelConfig.vue` 页面：模型列表表格 + 刷新状态按钮
- [x] 7.4 新增路由 `/embed-models` 指向 EmbedModelConfig 页面
- [x] 7.5 侧边栏导航增加"模型配置"入口

## 8. 前端 — 项目创建表单

- [x] 8.1 修改 `ProjectList.vue` 创建项目弹窗，新增"嵌入模型"下拉选择（仅 online 模型）
- [x] 8.2 修改 `api/project.ts`，创建项目参数新增 embed_model_id
- [x] 8.3 修改 `api/model/projectModel.ts`，ProjectItem 新增 embed_model_name 和 embed_dimension，CreateProjectParams 新增 embed_model_id

## 9. 前端 — 文档相关

- [x] 9.1 修改上传弹窗，移除 embedder_model 相关字段
- [x] 9.2 修改 `api/document.ts`，uploadDocument 参数移除 embedder_model
- [x] 9.3 修改 `api/model/documentModel.ts`，DocumentItem 移除 embedder_model，UploadDocumentParams 移除 embedder_model
- [x] 9.4 修改 `DocumentList.vue` 详情 Drawer，嵌入模型改为从项目信息展示
