## MODIFIED Requirements

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
系统 SHALL 提供 migration 为 golden_dataset 表新增评测字段。

#### Scenario: Migration 执行
- **WHEN** 执行数据库 migration
- **THEN** golden_dataset 表新增 retrieved_chunk_ids TEXT[]、is_hit BOOLEAN、hit_rank INT、evaluated_at TIMESTAMPTZ 字段，默认值分别为 '{}'、NULL、NULL、NULL
