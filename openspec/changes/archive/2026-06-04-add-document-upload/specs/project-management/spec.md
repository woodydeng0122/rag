## ADDED Requirements

### Requirement: Create project
系统 SHALL 提供创建项目的 API 端点。

#### Scenario: Create a new project
- **WHEN** 用户通过 `POST /api/projects` 提交项目名称和描述
- **THEN** 系统在 project 表中创建一条记录，包含 id、name、description、created_at、updated_at

### Requirement: List projects
系统 SHALL 提供查询项目列表的 API 端点。

#### Scenario: List all projects
- **WHEN** 用户通过 `GET /api/projects` 查询
- **THEN** 系统返回所有项目列表，每条包含 id、name、description、created_at、updated_at

### Requirement: Get project detail
系统 SHALL 提供查询单个项目的 API 端点。

#### Scenario: Get project by id
- **WHEN** 用户通过 `GET /api/projects/{project_id}` 查询
- **THEN** 系统返回该项目详情及其下所有 document 记录

### Requirement: Project contains multiple documents
一个项目 SHALL 包含多个文档，文档通过 project_id 关联到项目。

#### Scenario: Upload files to a project
- **WHEN** 用户向同一项目上传多个文件和 zip
- **THEN** 所有文档的 project_id 指向该项目，项目下可见所有文档
