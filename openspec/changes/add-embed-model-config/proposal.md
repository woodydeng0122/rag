## Why

当前上传文档时 `embedder_model` 参数是假选择 — 前端传了但后端始终使用启动时全局固定的模型实例。用户无法真正选择 embedding 模型，且向量维度硬编码为 512，换模型会导致写入失败。需要一个真实的模型配置机制，让项目创建时选定模型，保证同一项目内向量空间一致。

## What Changes

- 新增 `embed_model` 数据表，注册可用的嵌入模型（名称、维度、状态）
- 系统启动时扫描本地 `models/` 目录，自动注册模型并标记 online/offline
- 新增 `check-status` API，前端可触发重新扫描更新模型状态
- `project` 表新增 `embed_model_id` 和 `embed_dimension` 字段，创建项目时选定模型，不可切换
- **BREAKING** `document` 表删除 `embedder_model` 字段（模型信息从项目推导）
- 前端项目创建表单增加模型选择（仅显示 online 模型）
- 前端新增模型配置页面，展示模型列表及状态，支持刷新状态

## Capabilities

### New Capabilities
- `embed-model-config`: 嵌入模型注册、状态管理、项目关联。覆盖数据表、扫描逻辑、API、前端配置页

### Modified Capabilities
- `project-management`: 项目创建时需选择嵌入模型，创建后不可切换
- `document-upload`: 上传文档时移除 `embedder_model` 参数，模型从项目继承
- `document-process`: 处理文档时从项目读取模型配置，动态加载对应 embedder 实例

## Impact

- **数据库**: 新增 `embed_model` 表，`project` 表加字段，`document` 表删字段，需迁移脚本
- **后端 API**: 新增模型列表/状态检查接口，修改项目创建接口，修改上传接口
- **后端核心**: `SentenceTransformerEmbedder` 需支持按模型名动态加载（模型缓存池），`ProcessDocumentUseCase` 从项目读取模型
- **前端**: 项目创建表单增加模型选择，新增模型配置页，上传弹窗移除模型相关字段
- **向量索引**: `embedding` 表的 `VECTOR(512)` 需改为动态维度，或按项目维度建索引
