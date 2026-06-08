## Requirements

### Requirement: Golden dataset CRUD API
系统 SHALL 提供黄金数据集的增删改查 API，所有操作按 project_id 隔离。

- `GET /api/projects/{pid}/golden` — 获取项目下所有黄金记录
- `POST /api/projects/{pid}/golden` — 新增一条黄金记录
- `PUT /api/golden/{id}` — 更新一条黄金记录
- `DELETE /api/golden/{id}` — 删除一条黄金记录

#### Scenario: 获取黄金数据集列表
- **WHEN** 请求 `GET /api/projects/{pid}/golden`
- **THEN** 返回该项目下所有黄金记录，按 created_at DESC 排序

#### Scenario: 新增黄金记录
- **WHEN** 请求 `POST /api/projects/{pid}/golden`，body 包含 query、ground_truth_chunks、reference_answer
- **THEN** 创建记录并返回完整对象（含 id、created_at）

#### Scenario: 更新黄金记录
- **WHEN** 请求 `PUT /api/golden/{id}`，body 包含 query、ground_truth_chunks、reference_answer
- **THEN** 更新记录并返回更新后的对象

#### Scenario: 删除黄金记录
- **WHEN** 请求 `DELETE /api/golden/{id}`
- **THEN** 删除该记录，返回成功确认

#### Scenario: 删除不存在的记录
- **WHEN** 请求 `DELETE /api/golden/{id}` 且 id 不存在
- **THEN** 返回 404 错误

### Requirement: Golden dataset entity
GoldenRecord 实体 SHALL 包含 id、project_id、query、ground_truth_chunks、reference_answer、retrieved_chunk_ids、is_hit、hit_rank、evaluated_at、created_at 字段。

#### Scenario: 新建 GoldenRecord 默认值
- **WHEN** 创建新的 GoldenRecord
- **THEN** retrieved_chunk_ids 默认为空列表，is_hit 默认为 None，hit_rank 默认为 None，evaluated_at 默认为 None

### Requirement: Golden dataset repository port
系统 SHALL 提供 GoldenDatasetRepositoryPort 端口，定义 save、get_by_id、list_by_project、update、delete 方法。

#### Scenario: list_by_project 按项目查询
- **WHEN** 调用 list_by_project(project_id)
- **THEN** 返回该项目下所有黄金记录

### Requirement: PG golden dataset repository
系统 SHALL 提供 PgGoldenDatasetRepository 实现，使用 PostgreSQL 存储黄金数据集。

#### Scenario: 保存并回读
- **WHEN** 保存一条新记录后再按 id 查询
- **THEN** 查询结果与保存数据一致

### Requirement: Golden dataset frontend page
系统 SHALL 提供黄金数据集管理页面，路径为 `/golden`，依赖 activeProjectStore 获取当前项目。

#### Scenario: 未选择项目时
- **WHEN** 用户进入黄金数据集页面但未激活项目
- **THEN** 页面显示提示"请先选择一个项目"

#### Scenario: 已选择项目时
- **WHEN** 用户进入黄金数据集页面且已激活项目
- **THEN** 页面以表格展示该项目下的黄金记录

### Requirement: Golden dataset table display
表格 SHALL 展示查询文本、关联分块数、参考答案（截断）、评测状态、创建时间、操作列。

#### Scenario: 评测状态显示
- **WHEN** 记录的 is_hit 为 True
- **THEN** 显示"✅ 命中 (rank=N)"

#### Scenario: 未命中显示
- **WHEN** 记录的 is_hit 为 False
- **THEN** 显示"❌ 未命中"

#### Scenario: 未评测显示
- **WHEN** 记录的 evaluated_at 为 None
- **THEN** 显示"-- 未评测"

### Requirement: Golden dataset create/edit modal
系统 SHALL 提供弹窗用于新增和编辑黄金记录，包含查询文本输入、分块选择器、参考答案输入。

#### Scenario: 新增记录
- **WHEN** 用户点击"新增"按钮
- **THEN** 弹出空表单弹窗，标题为"新增黄金记录"

#### Scenario: 编辑记录
- **WHEN** 用户点击某行的"编辑"按钮
- **THEN** 弹出预填数据的弹窗，标题为"编辑黄金记录"

#### Scenario: 提交必填校验
- **WHEN** 用户提交时查询文本为空或未选择任何分块
- **THEN** 显示校验提示，不提交

### Requirement: Golden dataset batch operations
系统 SHALL 支持批量评测和批量删除，交互参考文档管理页。

#### Scenario: 批量评测
- **WHEN** 用户选中多条记录并点击"批量评测"
- **THEN** 弹出确认弹窗，确认后逐条执行评测，完成后提示"评测完成，项目评测数据已更新"

#### Scenario: 批量删除
- **WHEN** 用户选中多条记录并点击"批量删除"
- **THEN** 弹出确认弹窗，确认后执行删除，完成后刷新列表

#### Scenario: 选中数量显示
- **WHEN** 用户选中 N 条记录
- **THEN** 工具栏按钮显示选中数量，如"批量评测 (3)"

### Requirement: Golden dataset sidebar menu entry
侧边栏 SHALL 新增"黄金数据集"菜单项，图标使用 TrophyOutlined，路径为 `/golden`。

#### Scenario: 菜单导航
- **WHEN** 用户点击侧边栏"黄金数据集"
- **THEN** 导航到 `/golden` 页面
