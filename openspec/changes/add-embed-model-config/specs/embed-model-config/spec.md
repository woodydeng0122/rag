## ADDED Requirements

### Requirement: Embed model data table
系统 SHALL 提供 `embed_model` 数据表，存储嵌入模型的注册信息。

#### Scenario: Table schema
- **WHEN** 系统初始化数据库
- **THEN** 创建 `embed_model` 表，包含字段：id (UUID PK)、name (VARCHAR(255) UNIQUE)、dimension (INT)、description (TEXT)、status (VARCHAR(32), 默认 'offline')、created_at (TIMESTAMPTZ)、updated_at (TIMESTAMPTZ)

### Requirement: Auto scan models directory
系统 SHALL 在启动时自动扫描本地 `models/` 目录，将发现的模型注册到 `embed_model` 表。

#### Scenario: Discover new model
- **WHEN** `models/` 目录下存在子目录 `BAAI/bge-small-zh-v1.5/` 且包含 `config.json`
- **THEN** 系统在 `embed_model` 表中插入记录，name 为 `BAAI/bge-small-zh-v1.5`，dimension 从 `config.json` 的 `hidden_size` 字段读取，status 为 `online`

#### Scenario: Model directory missing
- **WHEN** `embed_model` 表中已有 `BAAI/bge-large-zh-v1.5` 记录，但 `models/` 目录下不存在该子目录
- **THEN** 该记录的 status 更新为 `offline`

#### Scenario: Model already registered
- **WHEN** 扫描发现 `BAAI/bge-small-zh-v1.5` 已存在于 `embed_model` 表
- **THEN** 更新 dimension 和 status，不重复插入

### Requirement: Check model status API
系统 SHALL 提供 `POST /api/embed-models/check-status` 端点，触发重新扫描 `models/` 目录并更新所有模型状态。

#### Scenario: Trigger status check
- **WHEN** 前端调用 `POST /api/embed-models/check-status`
- **THEN** 系统重新扫描 `models/` 目录，更新 `embed_model` 表中所有记录的 status，返回更新后的模型列表

### Requirement: List embed models API
系统 SHALL 提供 `GET /api/embed-models` 端点，返回所有已注册的嵌入模型列表。

#### Scenario: List all models
- **WHEN** 前端调用 `GET /api/embed-models`
- **THEN** 系统返回所有 `embed_model` 记录，包含 id、name、dimension、description、status

### Requirement: Embed model config page
前端 SHALL 提供嵌入模型配置页面，展示所有已注册模型及其状态。

#### Scenario: View model list
- **WHEN** 用户访问模型配置页
- **THEN** 页面展示模型列表表格，包含列：模型名称、维度、状态（online/offline 标签）、描述

#### Scenario: Refresh model status
- **WHEN** 用户点击"刷新状态"按钮
- **THEN** 前端调用 check-status API，更新后刷新列表

### Requirement: Project embed model association
系统 SHALL 在 `project` 表中关联嵌入模型，创建时选定，不可切换。

#### Scenario: Project table fields
- **WHEN** 系统初始化数据库
- **THEN** `project` 表包含 `embed_model_id` (UUID, REFERENCES embed_model(id)) 和 `embed_dimension` (INT, 默认 512) 字段

#### Scenario: Create project with model
- **WHEN** 用户创建项目并选择 `BAAI/bge-small-zh-v1.5` 模型
- **THEN** project 记录的 embed_model_id 指向该模型，embed_dimension 为 512

#### Scenario: Create project with offline model
- **WHEN** 用户创建项目时选择 status 为 offline 的模型
- **THEN** 系统返回 400 错误，提示所选模型不可用

#### Scenario: Switch model after creation
- **WHEN** 项目已创建后尝试修改 embed_model_id
- **THEN** 系统拒绝修改，返回错误提示

### Requirement: Project creation form model selector
前端 SHALL 在项目创建表单中提供模型选择下拉框，仅显示 online 模型。

#### Scenario: Model selector on create
- **WHEN** 用户打开项目创建表单
- **THEN** 表单包含"嵌入模型"下拉框，选项仅包含 status 为 online 的模型，显示模型名称和维度

### Requirement: Dynamic embedder loading
系统 SHALL 根据项目的 embed_model_id 动态加载对应的 SentenceTransformer 模型实例。

#### Scenario: Load model on first use
- **WHEN** 处理文档时项目关联的模型首次被使用
- **THEN** 系统加载对应 SentenceTransformer 模型到内存，缓存实例供后续使用

#### Scenario: Use cached model instance
- **WHEN** 处理文档时项目关联的模型已在缓存中
- **THEN** 系统直接使用缓存的模型实例，不重复加载
