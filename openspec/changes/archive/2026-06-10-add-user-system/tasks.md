## 1. 后端 — User 领域层

- [x] 1.1 创建 User 实体（`src/rag/domain/entities/user.py`），包含 id、username、password_hash、created_at 字段
- [x] 1.2 创建 UserRepository port（`src/rag/domain/ports/user_repository.py`），定义 get_by_id、get_by_username、list_all、create、update_password、delete 方法

## 2. 后端 — JWT 与密码基础设施

- [x] 2.1 创建 JWT 工具模块（`src/rag/infra/auth/jwt_handler.py`），实现 create_access_token 和 verify_token
- [x] 2.2 创建密码工具模块（`src/rag/infra/auth/password.py`），实现 hash_password 和 verify_password（bcrypt）
- [x] 2.3 在 Settings 中新增 jwt_secret_key 和 jwt_expire_hours 配置项

## 3. 后端 — User 基础设施层

- [x] 3.1 创建数据库迁移脚本（`src/rag/infra/database/migrations/012_user_system.sql`）：创建 user 表、改造 profile 表（新增 user_id + UNIQUE，迁移单例数据）、project 表新增 user_id
- [x] 3.2 创建 PgUserRepository 实现（`src/rag/infra/repositories/pg_user_repository.py`）

## 4. 后端 — Auth 应用层与 API

- [x] 4.1 创建 AuthUseCase（`src/rag/application/usecases/auth.py`），实现登录验证逻辑
- [x] 4.2 创建 FastAPI 认证依赖 `get_current_user`（`src/rag/adapters/api/dependencies.py`），从 Bearer Token 解析用户
- [x] 4.3 创建 Auth API schemas（`src/rag/adapters/api/schemas/auth.py`），定义 LoginRequest、TokenResponse、UserInfo
- [x] 4.4 创建 Auth 路由（`src/rag/adapters/api/routes/auth.py`），实现 POST /api/auth/login 和 GET /api/auth/me
- [x] 4.5 在 Container 中注册 user_repo 和 auth 相关依赖
- [x] 4.6 在 app.py 中挂载 auth 路由

## 5. 后端 — User 管理 API

- [x] 5.1 创建 User API schemas（`src/rag/adapters/api/schemas/user.py`），定义 CreateUserRequest、UpdateUserRequest、UserResponse
- [x] 5.2 创建 User 路由（`src/rag/adapters/api/routes/user.py`），实现 GET /api/users、POST /api/users、PUT /api/users/{id}、DELETE /api/users/{id}
- [x] 5.3 在 app.py 中挂载 user 路由

## 6. 后端 — 数据隔离改造

- [x] 6.1 改造 Profile 实体（`src/rag/domain/entities/profile.py`），新增 user_id 字段
- [x] 6.2 改造 ProfileRepository port 和 PgProfileRepository，所有方法增加 user_id 参数
- [x] 6.3 改造 Project 实体，新增 user_id 字段
- [x] 6.4 改造 ProjectRepository port 和 PgProjectRepository，查询方法增加 user_id 过滤
- [x] 6.5 改造所有现有 UseCase，注入 current_user，按 user_id 过滤数据
- [x] 6.6 改造所有现有路由，添加 `Depends(get_current_user)` 认证依赖
- [x] 6.7 改造 ProfileUseCase 和路由，支持 per-user profile

## 7. 后端 — CLI 创建用户

- [x] 7.1 创建 CLI 命令（`src/rag/adapters/cli/create_user.py`），实现 `python -m rag create-user --username --password`
- [x] 7.2 注册 CLI 命令到 registry

## 8. 前端 — 登录与认证

- [x] 8.1 创建 auth API 模块（`rag-web/src/api/auth.ts`），定义 login、getMe 方法
- [x] 8.2 创建 user Store（`rag-web/src/store/user.ts`），管理 token 和用户信息
- [x] 8.3 改造 request.ts：请求拦截器附加 Bearer token，响应拦截器处理 401
- [x] 8.4 创建 Login.vue 登录页面
- [x] 8.5 改造路由配置：添加 /login 路由，实现路由守卫（未登录跳 /login，已登录跳 /dashboard）

## 9. 前端 — 用户管理页面

- [x] 9.1 创建 user API 模块（`rag-web/src/api/user.ts`），定义 CRUD 方法
- [x] 9.2 创建 UserList.vue 用户管理页面，包含用户列表表格、新建/修改密码/删除操作
- [x] 9.3 在侧边栏菜单添加"用户管理"入口
- [x] 9.4 在路由配置中添加 /users 路由

## 10. 前端 — Header 用户信息

- [x] 10.1 改造 BasicLayout.vue Header 右侧：显示当前用户名 + 退出按钮
