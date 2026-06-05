## ADDED Requirements

### Requirement: Profile 数据模型
系统 SHALL 提供 profile 表，仅包含 `id`（固定为 1）和 `active_project_id`（UUID，可空，引用 project.id）两个字段。表中 SHALL 只有一行数据。

#### Scenario: 初始化 profile
- **WHEN** 系统首次启动，profile 表无数据
- **THEN** 首次 GET /api/profile 返回 `{ id: "1", active_project_id: null }`，自动创建默认行

#### Scenario: profile 表只有一行
- **WHEN** 任何写入操作执行
- **THEN** 始终使用 UPSERT（INSERT ON CONFLICT DO UPDATE），保证表中只有 id=1 的单行

### Requirement: 获取激活项目
系统 SHALL 提供 `GET /api/profile` 接口，返回当前 profile 记录，包含 `id` 和 `active_project_id`。

#### Scenario: 已设置激活项目
- **WHEN** GET /api/profile 且 active_project_id 不为空
- **THEN** 返回 `{ id: "1", active_project_id: "<uuid>" }`

#### Scenario: 未设置激活项目
- **WHEN** GET /api/profile 且 active_project_id 为 null
- **THEN** 返回 `{ id: "1", active_project_id: null }`

### Requirement: 更新激活项目
系统 SHALL 提供 `PUT /api/profile` 接口，接收 `{ active_project_id: "<uuid>" | null }`，更新 profile 记录。

#### Scenario: 设置激活项目
- **WHEN** PUT /api/profile 且 active_project_id 指向一个存在的项目
- **THEN** 更新 profile 的 active_project_id 并返回更新后的 profile 记录

#### Scenario: 设置不存在的项目
- **WHEN** PUT /api/profile 且 active_project_id 指向不存在的项目
- **THEN** 返回 404 错误，提示"项目不存在"

#### Scenario: 清空激活项目
- **WHEN** PUT /api/profile 且 active_project_id 为 null
- **THEN** 将 profile 的 active_project_id 设为 null 并返回更新后的记录

### Requirement: Profile 仓储接口
系统 SHALL 定义 ProfileRepositoryPort 接口，包含 `get()` 和 `upsert(active_project_id: str | None)` 方法，遵循 Clean Architecture 依赖规则。

#### Scenario: 仓储获取 profile
- **WHEN** 调用 profile_repo.get()
- **THEN** 返回 Profile 实体，若表为空则返回 active_project_id 为空字符串的默认实体

#### Scenario: 仓储更新 profile
- **WHEN** 调用 profile_repo.upsert(active_project_id)
- **THEN** 使用 UPSERT 语义写入数据库，返回更新后的 Profile 实体

### Requirement: Profile 数据库迁移
系统 SHALL 提供迁移脚本创建 profile 表，包含 `id INT PRIMARY KEY DEFAULT 1` 和 `active_project_id UUID REFERENCES project(id) ON DELETE SET NULL`。

#### Scenario: 执行迁移
- **WHEN** 运行数据库迁移
- **THEN** 创建 profile 表，并插入一行默认数据 `(id=1, active_project_id=NULL)`

#### Scenario: 激活项目被删除
- **WHEN** 被设为激活项目的项目被删除
- **THEN** profile 的 active_project_id 自动置为 NULL（ON DELETE SET NULL）
