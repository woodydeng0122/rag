## ADDED Requirements

### Requirement: Project 数据隔离
project 表 SHALL 新增 `user_id` 列（UUID, REFERENCES user(id) ON DELETE CASCADE），每个项目归属一个用户。用户只能访问自己的项目。

#### Scenario: 创建项目关联用户
- **WHEN** 用户创建项目
- **THEN** project.user_id 自动设为当前登录用户 ID

#### Scenario: 查询项目过滤
- **WHEN** 用户查询项目列表
- **THEN** 仅返回 user_id 等于当前用户 ID 的项目

#### Scenario: 访问他人项目
- **WHEN** 用户尝试访问不属于自己的项目
- **THEN** 返回 404 错误

### Requirement: Profile per-user
profile 表 SHALL 改造为 per-user 模式，新增 `user_id` 列（UUID, REFERENCES user(id) ON DELETE CASCADE, UNIQUE），每个用户一行配置。

#### Scenario: 获取 profile
- **WHEN** 用户请求 GET /api/profile
- **THEN** 返回该用户的 profile 记录

#### Scenario: 更新 profile
- **WHEN** 用户请求 PUT /api/profile
- **THEN** 更新该用户的 profile 记录

#### Scenario: 新用户 profile 自动创建
- **WHEN** 新用户首次访问 profile
- **THEN** 自动创建该用户的 profile 行（active_project_id 为 NULL）

### Requirement: 数据库迁移 — 现有数据归属
迁移脚本 SHALL 将现有 project 数据关联到首个 CLI 创建的用户，将现有单例 profile 数据迁移到该用户的 profile 行。

#### Scenario: 现有项目归属
- **WHEN** 执行迁移时已有 project 数据
- **THEN** 这些 project 的 user_id 设为迁移参数指定的用户 ID

#### Scenario: 现有 profile 迁移
- **WHEN** 执行迁移时已有单例 profile 数据
- **THEN** 将该行迁移为指定用户的 profile，删除原单例行

### Requirement: 前端登录页
前端 SHALL 提供登录页面（`/login`），包含用户名和密码输入框及登录按钮。

#### Scenario: 登录成功
- **WHEN** 输入正确凭据并点击登录
- **THEN** 存储 token 到 localStorage，跳转到 /dashboard

#### Scenario: 登录失败
- **WHEN** 输入错误凭据
- **THEN** 显示错误提示，停留在登录页

### Requirement: 前端路由守卫
前端 SHALL 实现路由守卫，未登录用户访问任何页面时重定向到 /login，已登录用户访问 /login 时重定向到 /dashboard。

#### Scenario: 未登录访问受保护页面
- **WHEN** 未登录用户访问 /dashboard 等页面
- **THEN** 重定向到 /login

#### Scenario: 已登录访问登录页
- **WHEN** 已登录用户访问 /login
- **THEN** 重定向到 /dashboard

### Requirement: 前端 token 拦截器
前端 axios 请求拦截器 SHALL 自动在请求头中附加 `Authorization: Bearer <token>`，响应拦截器 SHALL 处理 401 状态码（清除 token 并跳转登录页）。

#### Scenario: 请求附加 token
- **WHEN** 发起 API 请求且 localStorage 中有 token
- **THEN** 请求头自动附加 Authorization

#### Scenario: 401 响应处理
- **WHEN** API 返回 401 状态码
- **THEN** 清除 localStorage 中的 token，跳转到 /login

### Requirement: 前端 Header 用户信息
BasicLayout Header 右侧 SHALL 显示当前登录用户名和退出按钮。

#### Scenario: 显示用户名
- **WHEN** 用户已登录
- **THEN** Header 右侧显示用户名

#### Scenario: 退出登录
- **WHEN** 点击退出按钮
- **THEN** 清除 token，跳转到 /login
