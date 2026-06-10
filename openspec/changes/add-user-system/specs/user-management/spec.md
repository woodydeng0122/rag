## ADDED Requirements

### Requirement: 用户列表
系统 SHALL 提供 `GET /api/users` 接口（需认证），返回所有用户列表 `[{ id, username, created_at }]`，不返回 password_hash。

#### Scenario: 获取用户列表
- **WHEN** GET /api/users 且已认证
- **THEN** 返回用户列表，每项包含 id、username、created_at

### Requirement: 创建用户
系统 SHALL 提供 `POST /api/users` 接口（需认证），接收 `{ username, password }`，创建新用户。

#### Scenario: 创建成功
- **WHEN** POST /api/users 且用户名不存在
- **THEN** 返回 201，包含新用户信息 `{ id, username, created_at }`

#### Scenario: 用户名已存在
- **WHEN** POST /api/users 且用户名已存在
- **THEN** 返回 409 错误，提示"用户名已存在"

#### Scenario: 参数校验
- **WHEN** POST /api/users 且 username 或 password 为空
- **THEN** 返回 422 错误

### Requirement: 修改用户密码
系统 SHALL 提供 `PUT /api/users/{id}` 接口（需认证），接收 `{ password }`，修改指定用户密码。

#### Scenario: 修改成功
- **WHEN** PUT /api/users/{id} 且用户存在
- **THEN** 更新密码哈希，返回用户信息

#### Scenario: 用户不存在
- **WHEN** PUT /api/users/{id} 且用户不存在
- **THEN** 返回 404 错误

### Requirement: 删除用户
系统 SHALL 提供 `DELETE /api/users/{id}` 接口（需认证），删除指定用户。

#### Scenario: 删除成功
- **WHEN** DELETE /api/users/{id} 且用户存在
- **THEN** 删除用户及其关联数据（profile），返回 204

#### Scenario: 用户不存在
- **WHEN** DELETE /api/users/{id} 且用户不存在
- **THEN** 返回 404 错误

#### Scenario: 删除自己
- **WHEN** DELETE /api/users/{id} 且 id 为当前登录用户
- **THEN** 返回 400 错误，提示"不能删除当前登录用户"

### Requirement: 前端用户管理页面
前端 SHALL 在侧边栏提供"用户管理"菜单入口，点击进入用户列表页面，支持创建用户、修改密码、删除用户操作。

#### Scenario: 用户列表展示
- **WHEN** 进入用户管理页面
- **THEN** 显示用户列表表格，包含用户名、创建时间、操作列

#### Scenario: 创建用户
- **WHEN** 点击"新建用户"按钮
- **THEN** 弹出模态框，输入用户名和密码，提交后刷新列表

#### Scenario: 修改密码
- **WHEN** 点击某用户的"修改密码"按钮
- **THEN** 弹出模态框，输入新密码，提交后提示成功

#### Scenario: 删除用户
- **WHEN** 点击某用户的"删除"按钮
- **THEN** 弹出确认框，确认后删除并刷新列表
