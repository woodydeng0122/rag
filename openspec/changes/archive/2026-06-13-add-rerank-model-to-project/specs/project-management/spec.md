## MODIFIED Requirements

### Requirement: Create project
系统 SHALL 提供创建项目的 API 端点，支持可选的 `rerank_model_id` 参数。

#### Scenario: Create a new project without rerank model
- **WHEN** 用户通过 `POST /api/projects` 提交项目名称和描述，不传 `rerank_model_id`
- **THEN** 系统在 project 表中创建一条记录，`rerank_model_id` 为 NULL

#### Scenario: Create a new project with rerank model
- **WHEN** 用户通过 `POST /api/projects` 提交项目名称、描述和 `rerank_model_id`
- **THEN** 系统校验 `rerank_model_id` 对应的 `embed_model.model_type` 为 `"reranker"`，校验通过后创建项目记录

#### Scenario: Create project with invalid rerank_model_id
- **WHEN** 用户传入的 `rerank_model_id` 对应的 `embed_model.model_type` 为 `"embed"`
- **THEN** 返回 400 错误，提示"指定的模型不是重排模型"

### Requirement: Get project detail
系统 SHALL 提供查询单个项目的 API 端点，响应包含重排模型信息。

#### Scenario: Get project by id
- **WHEN** 用户通过 `GET /api/projects/{project_id}` 查询
- **THEN** 系统返回该项目详情，包含 `rerank_model_id`、`rerank_model_name` 字段；若未配置重排模型，`rerank_model_id` 为空字符串，`rerank_model_name` 为空字符串

### Requirement: List projects
系统 SHALL 提供查询项目列表的 API 端点，每条包含重排模型信息。

#### Scenario: List all projects
- **WHEN** 用户通过 `GET /api/projects` 查询
- **THEN** 系统返回所有项目列表，每条包含 `rerank_model_id`、`rerank_model_name` 字段
