## MODIFIED Requirements

### Requirement: GoldenRecord entity with metadata
GoldenRecord 实体 SHALL 新增 metadata 字段，类型为 dict，默认为空字典。

#### Scenario: 新建记录默认 metadata
- **WHEN** 创建新的 GoldenRecord
- **THEN** metadata 默认为空字典 `{}`

#### Scenario: 导入记录带 metadata
- **WHEN** 通过导入创建 GoldenRecord 且源数据含 metadata
- **THEN** metadata 字段保留源数据的完整信息

### Requirement: Golden dataset database migration for metadata
系统 SHALL 提供 migration 为 golden_dataset 表新增 metadata JSONB 字段。

#### Scenario: Migration 执行
- **WHEN** 执行数据库 migration
- **THEN** golden_dataset 表新增 metadata JSONB DEFAULT '{}' 字段

### Requirement: Golden dataset API response includes metadata
黄金数据集 API 响应 SHALL 包含 metadata 字段。

#### Scenario: 列表响应
- **WHEN** 请求 `GET /api/projects/{pid}/golden-datasets`
- **THEN** 每条记录包含 metadata 字段

#### Scenario: 创建/更新响应
- **WHEN** 创建或更新黄金记录
- **THEN** 响应包含 metadata 字段
