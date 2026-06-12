# Rerank Model Config

## Purpose

重排模型的项目级配置能力 — 扩展 embed_model 注册表支持 model_type 区分、项目表新增 rerank_model_id FK、扫描器自动识别模型类型、RerankerPool 缓存管理、用例适配及前端表单支持。

## Requirements

### Requirement: embed_model table supports model_type column
`embed_model` 表 SHALL 新增 `model_type` 列，取值为 `"embed"` 或 `"reranker"`，用于区分嵌入模型和重排模型。

#### Scenario: Migration 执行
- **WHEN** 执行数据库 migration
- **THEN** `embed_model` 表新增 `model_type VARCHAR(32) NOT NULL DEFAULT 'embed'` 列，已有行自动设为 `"embed"`

#### Scenario: 新增嵌入模型
- **WHEN** 扫描发现嵌入模型并写入 `embed_model` 表
- **THEN** `model_type` 设为 `"embed"`

#### Scenario: 新增重排模型
- **WHEN** 扫描发现重排模型并写入 `embed_model` 表
- **THEN** `model_type` 设为 `"reranker"`，`dimension` 设为 0

### Requirement: ModelScanner auto-detects model_type
`ModelScanner` 扫描时 SHALL 通过 `modules.json` 是否存在自动判定模型类型。

#### Scenario: 嵌入模型识别
- **WHEN** 模型目录下存在 `modules.json`
- **THEN** `model_type` 判定为 `"embed"`，`dimension` 从 `config.json` 的 `hidden_size` 读取

#### Scenario: 重排模型识别
- **WHEN** 模型目录下不存在 `modules.json`
- **THEN** `model_type` 判定为 `"reranker"`，`dimension` 设为 0

### Requirement: ScannedModel includes model_type
`ScannedModel` 值对象 SHALL 包含 `model_type` 字段。

#### Scenario: 扫描结果包含 model_type
- **WHEN** `ModelScanner.scan()` 返回结果
- **THEN** 每个 `ScannedModel` 包含 `model_type: "embed" | "reranker"` 字段

### Requirement: EmbedModel entity supports model_type
`EmbedModel` 实体 SHALL 包含 `model_type` 字段，且 `ensure_complete()` 按 `model_type` 差异化校验。

#### Scenario: embed 类型校验 dimension
- **WHEN** `model_type == "embed"` 且 `dimension == 0`
- **THEN** 抛出 `ValueError`

#### Scenario: reranker 类型跳过 dimension 校验
- **WHEN** `model_type == "reranker"` 且 `dimension == 0`
- **THEN** 不抛出异常，校验通过

### Requirement: project table supports rerank_model_id
`project` 表 SHALL 新增 `rerank_model_id` FK 列，指向 `embed_model` 表中 `model_type="reranker"` 的行。

#### Scenario: Migration 执行
- **WHEN** 执行数据库 migration
- **THEN** `project` 表新增 `rerank_model_id UUID REFERENCES embed_model(id) DEFAULT NULL` 列，已有行自动设为 NULL

#### Scenario: 创建项目时指定重排模型
- **WHEN** 创建项目时传入 `rerank_model_id`
- **THEN** `project` 表存储该 FK，且对应的 `embed_model.model_type` 必须为 `"reranker"`

#### Scenario: 创建项目时不指定重排模型
- **WHEN** 创建项目时不传 `rerank_model_id`
- **THEN** `rerank_model_id` 为 NULL，表示该项目不使用重排

### Requirement: Project entity supports rerank_model_id
`Project` 实体 SHALL 包含 `rerank_model_id` 字段。

#### Scenario: Project 实体字段
- **WHEN** 从持久化层重建 Project 实体
- **THEN** 实体包含 `rerank_model_id: str` 字段，默认为空字符串

### Requirement: RerankerPool caches CrossEncoder instances
系统 SHALL 提供 `RerankerPool`，按 `model_path` 缓存 `CrossEncoder` 实例。

#### Scenario: 首次获取模型
- **WHEN** 请求 `model_path="models/BAAI/bge-reranker-base"` 且池中无缓存
- **THEN** 加载 `CrossEncoder(model_path)` 并缓存，返回实例

#### Scenario: 重复获取模型
- **WHEN** 请求已缓存的 `model_path`
- **THEN** 直接返回缓存实例，不重复加载

#### Scenario: 超出 max_size
- **WHEN** 缓存数量超过 `max_size`
- **THEN** 淘汰最早未使用的实例

### Requirement: GoldenRerankUseCase uses project-specific rerank model
`GoldenRerankUseCase` SHALL 从项目配置获取重排模型，通过 `RerankerPool` 获取实例。

#### Scenario: 项目配置了重排模型
- **WHEN** 触发重排且 `project.rerank_model_id` 不为空
- **THEN** 从 `embed_model` 表获取模型路径，通过 `RerankerPool.get(model_path)` 获取 `CrossEncoder` 实例执行重排

#### Scenario: 项目未配置重排模型
- **WHEN** 触发重排且 `project.rerank_model_id` 为空
- **THEN** 抛出 `ValueError`，提示"项目未配置重排模型"

#### Scenario: 重排结果记录 model_name
- **WHEN** 重排完成并持久化 `GoldenRerank`
- **THEN** `model_name` 字段记录实际使用的重排模型名称（从 `embed_model.name` 获取），而非硬编码

### Requirement: ScanEmbedModelsUseCase writes model_type
`ScanEmbedModelsUseCase` 扫描并注册模型时 SHALL 写入 `model_type` 字段。

#### Scenario: 扫描结果按类型注册
- **WHEN** 扫描发现嵌入模型
- **THEN** 注册到 `embed_model` 表，`model_type="embed"`

#### Scenario: 扫描发现重排模型
- **WHEN** 扫描发现重排模型
- **THEN** 注册到 `embed_model` 表，`model_type="reranker"`，`dimension=0`

### Requirement: PgEmbedModelRepository supports model_type
`PgEmbedModelRepository` 的所有 SQL SHALL 适配 `model_type` 列。

#### Scenario: 保存模型时写入 model_type
- **WHEN** 保存 `EmbedModel` 实体
- **THEN** INSERT/UPDATE 语句包含 `model_type` 字段

#### Scenario: 查询时可按 model_type 过滤
- **WHEN** 需要查询特定类型的模型
- **THEN** 支持 `WHERE model_type = ?` 过滤条件

### Requirement: PgProjectRepository supports rerank_model_id
`PgProjectRepository` 的所有 SQL SHALL 适配 `rerank_model_id` 列。

#### Scenario: 保存项目时写入 rerank_model_id
- **WHEN** 保存 `Project` 实体
- **THEN** INSERT/UPDATE 语句包含 `rerank_model_id` 字段

#### Scenario: 查询项目时返回 rerank_model_id
- **WHEN** 从数据库读取项目
- **THEN** SELECT 和 `_row_to_project` 包含 `rerank_model_id` 字段

### Requirement: 前端项目表单支持重排模型选择
项目创建/编辑表单 SHALL 新增重排模型选择下拉框，数据来源为 `model_type="reranker"` 的在线模型列表。

#### Scenario: 新建项目时选择重排模型
- **WHEN** 用户点击新建项目
- **THEN** 表单显示"重排模型"下拉框（可选），选项为所有 `model_type="reranker"` 且 `status="online"` 的模型

#### Scenario: 不选择重排模型
- **WHEN** 用户创建项目时不选择重排模型
- **THEN** `rerank_model_id` 为空，项目不使用重排

#### Scenario: 编辑项目时重排模型不可修改
- **WHEN** 用户编辑已有项目
- **THEN** "重排模型"下拉框为禁用状态，与嵌入模型行为一致

### Requirement: 前端项目卡片展示重排模型
项目卡片 SHALL 展示重排模型名称。

#### Scenario: 项目配置了重排模型
- **WHEN** 项目卡片渲染且项目有 `rerank_model_name`
- **THEN** 卡片上显示重排模型名称标签

#### Scenario: 项目未配置重排模型
- **WHEN** 项目卡片渲染且项目无重排模型
- **THEN** 卡片上不显示重排模型标签

### Requirement: 前端 EmbedModelItem 类型支持 model_type
前端 `EmbedModelItem` 接口 SHALL 包含 `model_type` 字段。

#### Scenario: 模型列表 API 响应
- **WHEN** 前端获取模型列表
- **THEN** 每个模型对象包含 `model_type: "embed" | "reranker"` 字段

### Requirement: 前端 EmbedModelStore 支持按 model_type 过滤
`useEmbedModelStore` SHALL 提供 `onlineEmbedModels` 和 `onlineRerankerModels` 计算属性。

#### Scenario: 获取嵌入模型列表
- **WHEN** 组件使用 `embedModelStore.onlineEmbedModels`
- **THEN** 返回 `model_type="embed"` 且 `status="online"` 的模型列表

#### Scenario: 获取重排模型列表
- **WHEN** 组件使用 `embedModelStore.onlineRerankerModels`
- **THEN** 返回 `model_type="reranker"` 且 `status="online"` 的模型列表

### Requirement: 前端模型配置页表格展示 model_type
模型配置页表格 SHALL 新增"类型"列，展示模型的 `model_type`。

#### Scenario: 表格列定义
- **WHEN** 模型配置页渲染表格
- **THEN** 在"维度"列之前新增"类型"列，显示 `model_type` 对应的中文标签

#### Scenario: embed 类型标签
- **WHEN** 模型 `model_type` 为 `"embed"`
- **THEN** 显示蓝色标签"嵌入"

#### Scenario: reranker 类型标签
- **WHEN** 模型 `model_type` 为 `"reranker"`
- **THEN** 显示绿色标签"重排"

### Requirement: 前端模型配置页详情展示 model_type
模型详情 Drawer SHALL 展示 `model_type` 信息。

#### Scenario: 详情展示类型
- **WHEN** 用户点击模型"详情"按钮
- **THEN** Drawer 的 descriptions 中新增"模型类型"项，显示中文标签（嵌入/重排）

### Requirement: 前端新增模型时自动识别 model_type
新增模型弹窗 SHALL 根据模型名称自动识别 `model_type`，无需用户手动选择。

#### Scenario: 扫描注册的模型
- **WHEN** 通过"刷新状态"扫描发现新模型
- **THEN** `model_type` 由后端自动判定（基于 `modules.json`），前端无需处理

#### Scenario: 手动新增模型
- **WHEN** 用户手动填写模型名称新增模型
- **THEN** 后端根据本地模型目录自动判定 `model_type`，前端无需提供 `model_type` 输入

### Requirement: 前端模型配置页维度列按类型差异化展示
模型配置页表格"维度"列 SHALL 按 `model_type` 差异化展示。

#### Scenario: embed 类型展示维度
- **WHEN** 模型 `model_type` 为 `"embed"`
- **THEN** "维度"列正常显示数值（如 512）

#### Scenario: reranker 类型展示维度
- **WHEN** 模型 `model_type` 为 `"reranker"`
- **THEN** "维度"列显示 "-"（reranker 无向量维度概念）
