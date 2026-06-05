## MODIFIED Requirements

### Requirement: Create project
系统 SHALL 提供创建项目的 API 端点，创建时必须选择嵌入模型。

#### Scenario: Create a new project
- **WHEN** 用户通过 `POST /api/projects` 提交项目名称、描述和 embed_model_id
- **THEN** 系统在 project 表中创建一条记录，包含 id、name、description、embed_model_id、embed_dimension、created_at、updated_at

#### Scenario: Create project without model
- **WHEN** 用户提交创建项目请求但未提供 embed_model_id
- **THEN** 系统返回 400 错误，提示必须选择嵌入模型

#### Scenario: Create project with offline model
- **WHEN** 用户提交的 embed_model_id 对应的模型 status 为 offline
- **THEN** 系统返回 400 错误，提示所选模型不可用

### Requirement: List projects
系统 SHALL 提供查询项目列表的 API 端点，返回结果包含嵌入模型信息。

#### Scenario: List all projects
- **WHEN** 用户通过 `GET /api/projects` 查询
- **THEN** 系统返回所有项目列表，每条包含 id、name、description、embed_model_id、embed_dimension、embed_model_name（从 embed_model 表关联）、created_at、updated_at

### Requirement: Get project detail
系统 SHALL 提供查询单个项目的 API 端点，返回结果包含嵌入模型详情。

#### Scenario: Get project by id
- **WHEN** 用户通过 `GET /api/projects/{project_id}` 查询
- **THEN** 系统返回该项目详情，包含嵌入模型的名称和维度信息
