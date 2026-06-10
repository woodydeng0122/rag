## Why

当前系统无用户概念，所有数据全局共享，profile 表为单例（id=1），无法支持多人使用。需要接入用户体系，实现登录认证和数据隔离，使多个用户可以独立使用 RAG 管理端。

## What Changes

- 新增 `user` 数据库表，存储用户名和 bcrypt 哈希密码
- 新增 JWT 认证机制（用户名+密码登录，返回 access_token，24h 过期）
- 新增 Auth 中间件，验证请求中的 Bearer Token，注入当前用户上下文
- 改造 `profile` 表：从单例（id=1）变为 per-user，每个用户一行配置
- 改造 `project` 表：新增 `user_id` 字段，实现 project 级别数据隔离
- 新增 CLI 命令 `create-user`，管理员通过命令行创建账号（无注册功能）
- 前端新增登录页、路由守卫、token 拦截器
- 前端侧边栏新增用户管理菜单，支持管理员创建/删除/修改密码
- 前端 Header 右侧显示当前用户名和退出按钮

## Capabilities

### New Capabilities
- `user-auth`: 用户认证（JWT 登录/验证、Auth 中间件、CLI 创建用户）
- `user-management`: 用户管理（CRUD API + 前端用户管理页面）
- `data-isolation`: 数据隔离（project 加 user_id、profile 改 per-user、现有 UseCase 注入用户上下文）

### Modified Capabilities
- `active-project-profile`: profile 从单例改为 per-user，API 需携带用户上下文

## Impact

- **后端**: 新增 User 实体、UserRepository port、PgUserRepository、AuthUseCase、Auth 路由、User 路由、JWT 中间件；改造 Profile 实体/仓储、Project 实体/仓储；所有现有 UseCase 需注入 current_user
- **前端**: 新增 Login.vue、UserList.vue、auth API、user API、user Store；改造 request.ts（token 拦截器）、router（路由守卫）、BasicLayout（用户名+退出）
- **数据库**: 新增 012_user_system.sql 迁移（user 表 + profile 改造 + project 加 user_id）
- **CLI**: 新增 `python -m rag create-user` 命令
