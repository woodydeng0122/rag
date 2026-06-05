## ADDED Requirements

### Requirement: 激活项目全局 Store
前端 SHALL 提供 `useActiveProjectStore`（Pinia），包含 `activeProjectId`、`activeProject`（完整项目信息）、`setActiveProject(id)` 和 `fetchActiveProject()` 方法。Store 在 BasicLayout 初始化时自动加载。

#### Scenario: Store 初始化
- **WHEN** BasicLayout 组件挂载
- **THEN** 自动调用 fetchActiveProject() 从 API 加载激活项目信息

#### Scenario: 设置激活项目
- **WHEN** 调用 setActiveProject(id)
- **THEN** 调用 PUT /api/profile 更新后端，成功后更新 Store 中的 activeProjectId 和 activeProject

#### Scenario: 设置激活项目失败
- **WHEN** 调用 setActiveProject(id) 但 API 返回错误
- **THEN** Store 状态不变，显示错误提示

### Requirement: 项目页激活操作
项目列表页 SHALL 在每个项目卡片的 actions 区域增加"激活"按钮。点击后调用 Store 的 setActiveProject 方法。

#### Scenario: 点击激活按钮
- **WHEN** 用户点击某项目卡片的"激活"按钮
- **THEN** 调用 setActiveProject(project.id)，成功后该卡片显示为激活状态

#### Scenario: 激活当前已激活的项目
- **WHEN** 用户点击已是激活状态的项目的"激活"按钮
- **THEN** 无操作（幂等）

### Requirement: 激活项目卡片视觉区分
激活项目卡片 SHALL 有以下视觉特征：左侧 3px 主题色色带、背景色微升为 `#f0f7ff`、右下角显示"当前项目" Tag（a-tag color="blue"）。非激活项目卡片不显示"激活"按钮以外的额外标记。

#### Scenario: 激活项目卡片渲染
- **WHEN** 项目列表中某个项目是激活项目
- **THEN** 该卡片左侧显示 3px #1677ff 色带，背景为 #f0f7ff，actions 区域显示"当前项目" Tag 替代"激活"按钮

#### Scenario: 非激活项目卡片渲染
- **WHEN** 项目列表中某个项目不是激活项目
- **THEN** 该卡片无色带，背景为默认白色，actions 区域显示"激活"按钮

### Requirement: Header 常驻激活项目名
Header 中间区域 SHALL 常驻显示激活项目名称。无激活项目时显示"未选择项目"。点击项目名 SHALL 跳转到项目页。

#### Scenario: 有激活项目
- **WHEN** Store 中 activeProject 不为 null
- **THEN** Header 中间显示项目名称，点击跳转到 /projects

#### Scenario: 无激活项目
- **WHEN** Store 中 activeProject 为 null
- **THEN** Header 中间显示"未选择项目"（灰色文字），点击跳转到 /projects

### Requirement: 文档管理菜单入口
侧边栏 SHALL 新增"文档管理"菜单项，路由为 `/documents`，使用 FileTextOutlined 图标。

#### Scenario: 点击文档管理菜单
- **WHEN** 用户点击侧边栏"文档管理"
- **THEN** 跳转到 /documents 页面

### Requirement: 文档列表独立路由
文档列表 SHALL 使用独立路由 `/documents`，从 Store 读取 activeProjectId 加载对应项目的文档。移除原有 `/projects/:id/documents` 路由。

#### Scenario: 有激活项目时访问文档页
- **WHEN** 用户访问 /documents 且 Store 中 activeProjectId 不为空
- **THEN** 自动加载该项目的文档列表

#### Scenario: 无激活项目时访问文档页
- **WHEN** 用户访问 /documents 且 Store 中 activeProjectId 为空
- **THEN** 显示空状态提示"请先在项目页激活一个项目"，并提供跳转项目页的链接

#### Scenario: 旧路由不可用
- **WHEN** 用户访问 /projects/:id/documents
- **THEN** 路由不匹配，重定向到 /projects 或 404

### Requirement: 激活项目被删除时状态同步
当激活项目在项目页被删除时，Store SHALL 自动清空激活项目状态（依赖数据库 ON DELETE SET NULL + 下次 Store 刷新）。

#### Scenario: 删除激活项目
- **WHEN** 用户删除当前激活的项目
- **THEN** 项目删除成功后，Store 的 activeProjectId 和 activeProject 清空，Header 显示"未选择项目"
