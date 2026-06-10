## Context

RAG 管理端采用 Clean Architecture 分层（Domain / Application / Infrastructure / API），前端为 Vue3 + Pinia + Ant Design Vue。当前系统无用户概念，profile 表为单例（id=1），所有数据全局共享。需要接入用户体系，实现登录认证和数据隔离。

## Goals / Non-Goals

**Goals:**
- 接入 JWT 认证，用户名+密码登录，24h 过期
- 管理员通过 CLI 命令创建账号，无注册功能
- 所有用户平等，无角色权限
- project 级别数据隔离（project 加 user_id，下游通过 project_id 自然隔离）
- profile 从单例改为 per-user
- 前端登录页、路由守卫、token 拦截器
- 侧边栏用户管理菜单

**Non-Goals:**
- 不做用户自注册
- 不做角色权限体系（admin/viewer 等）
- 不做 OAuth2/SSO 对接
- 不做 refresh token 机制
- 不做全表 user_id 冗余（仅 project 级隔离）
- 不做密码找回/重置功能

## Decisions

### D1: 认证方式 — JWT Bearer Token

**选择**: 用户名+密码登录，后端返回 JWT access_token，前端请求携带 `Authorization: Bearer <token>`

**备选方案**:
- A. Session + Cookie — 需要服务端状态，不适合 API 服务
- B. OAuth2/SSO — 内部工具不需要，复杂度高

**理由**: JWT 无状态，适合 FastAPI API 服务；内部工具不需要 refresh token，24h 过期足够。

### D2: 数据隔离策略 — project 级别

**选择**: 仅在 project 表加 `user_id`，下游数据（document/chunk/embedding/golden/qa）通过 `project_id` 自然隔离

**备选方案**:
- A. 全表加 user_id — 冗余，破坏现有外键关系，改动大
- B. 行级安全策略（RLS）— PostgreSQL 特性，增加运维复杂度

**理由**: project 已是所有数据的根节点，下游均通过 project_id 关联。project 级隔离改动最小、语义最清晰。

### D3: Profile 改造 — 从单例到 per-user

**选择**: profile 表新增 `user_id` 列作为外键 + UNIQUE 约束，每个用户一行配置

**备选方案**:
- A. 删除 profile 表，active_project_id 存入 user 表 — 耦合用户实体和配置
- B. 保留单例 profile，加 user_id 过滤 — 语义混乱

**理由**: per-user profile 保持实体职责单一，与 user 表松耦合。UNIQUE(user_id) 保证一人一行。

### D4: 冷启动 — CLI 命令创建首个管理员

**选择**: `python -m rag create-user --username <name> --password <pwd>` 命令行创建

**备选方案**:
- A. 迁移脚本自动创建 admin — 迁移不应包含业务逻辑
- B. 首次启动检测 user 表为空自动创建 — 隐式行为，不可控

**理由**: CLI 命令显式、可控，与现有 CLI 风格一致。

### D5: 密码存储 — bcrypt

**选择**: 使用 bcrypt 哈希存储密码

**理由**: bcrypt 自带盐值、抗彩虹表、可调工作因子，是密码哈希的标准选择。

### D6: JWT 中间件实现 — FastAPI Dependency

**选择**: 使用 FastAPI 的 `Depends()` 机制实现认证依赖注入，而非 Starlette 中间件

**备选方案**:
- A. Starlette 中间件全局拦截 — 所有路由强制认证，健康检查等也需要处理
- B. FastAPI Depends 按需注入 — 灵活，可选择性保护路由

**理由**: Depends 方式更灵活，健康检查等路由无需认证；与 FastAPI 生态一致。

### D7: 前端 token 存储 — localStorage

**选择**: JWT 存储在 localStorage，请求拦截器自动附加 Authorization header

**备选方案**:
- A. Cookie — 需要后端设置，跨域处理复杂
- B. sessionStorage — 关闭标签页即失效，体验差

**理由**: localStorage 简单直接，适合内部工具；token 过期后前端跳转登录页即可。

## Risks / Trade-offs

- [现有数据归属] -> 迁移时需将现有 project 关联到某个用户（CLI 创建的首个用户），否则数据不可见
- [JWT 无刷新机制] -> 24h 后 token 过期需重新登录，内部工具可接受
- [无角色权限] -> 所有登录用户可管理所有用户账号，内部工具信任模型下可接受
- [profile 迁移] -> 现有单例 profile 数据需迁移到首个用户的 profile 行
- [并发创建用户] -> username UNIQUE 约束防止重复
