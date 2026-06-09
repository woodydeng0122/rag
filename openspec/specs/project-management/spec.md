# Project Management

## Purpose

提供项目的 CRUD API，项目是文档的容器，一个项目包含多个文档。

## Requirements

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

#### Scenario: 评估统计按钮
- **WHEN** 项目卡片渲染
- **THEN** actions 栏显示 BarChartOutlined 图标按钮，点击触发评估统计 Drawer

### Requirement: Project entity with evaluation fields
Project 实体 SHALL 新增评测汇总字段：eval_recall_at_10、eval_mrr、eval_answerable、eval_total、eval_latency_avg_ms、evaluated_at。

#### Scenario: 新项目默认值
- **WHEN** 创建新项目
- **THEN** 所有评测字段默认为 None/空，表示未评测

#### Scenario: 评测后更新
- **WHEN** 对项目执行评测
- **THEN** 项目评测字段更新为本次评测汇总值

### Requirement: Project API response includes evaluation fields
项目 API 响应 SHALL 包含评测汇总字段。

#### Scenario: 项目列表响应
- **WHEN** 请求 `GET /api/projects`
- **THEN** 每个项目对象包含 eval_recall_at_10、eval_mrr、eval_answerable、eval_total、eval_latency_avg_ms、evaluated_at 字段

#### Scenario: 项目详情响应
- **WHEN** 请求 `GET /api/projects/{id}`
- **THEN** 响应包含评测汇总字段

### Requirement: Project database migration
系统 SHALL 提供 migration 为 project 表新增评测字段。

#### Scenario: Migration 执行
- **WHEN** 执行数据库 migration
- **THEN** project 表新增 eval_recall_at_10 FLOAT、eval_mrr FLOAT、eval_answerable INT、eval_total INT、eval_latency_avg_ms FLOAT、evaluated_at TIMESTAMPTZ 字段，默认值为 NULL

### Requirement: Golden dataset database migration
系统 SHALL 提供 migration 为 golden 表新增评测字段。

#### Scenario: Migration 执行
- **WHEN** 执行数据库 migration
- **THEN** golden 表新增 retrieved_chunk_ids TEXT[]、is_hit BOOLEAN、hit_rank INT、evaluated_at TIMESTAMPTZ 字段，默认值分别为 '{}'、NULL、NULL、NULL
