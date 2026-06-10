## ADDED Requirements

### Requirement: User 数据模型
系统 SHALL 提供 user 表，包含 `id`（UUID 主键）、`username`（VARCHAR(255) UNIQUE NOT NULL）、`password_hash`（VARCHAR(255) NOT NULL）、`created_at`（TIMESTAMPTZ）字段。

#### Scenario: 用户名唯一
- **WHEN** 创建用户时 username 已存在
- **THEN** 返回 409 错误，提示"用户名已存在"

### Requirement: 用户登录
系统 SHALL 提供 `POST /api/auth/login` 接口，接收 `{ username, password }`，验证密码后返回 `{ access_token, token_type: "bearer" }`。

#### Scenario: 登录成功
- **WHEN** POST /api/auth/login 且用户名存在且密码正确
- **THEN** 返回 200，包含 JWT access_token（payload 含 user_id 和 username，24h 过期）

#### Scenario: 用户名不存在
- **WHEN** POST /api/auth/login 且用户名不存在
- **THEN** 返回 401 错误，提示"用户名或密码错误"

#### Scenario: 密码错误
- **WHEN** POST /api/auth/login 且密码不匹配
- **THEN** 返回 401 错误，提示"用户名或密码错误"

### Requirement: 获取当前用户
系统 SHALL 提供 `GET /api/auth/me` 接口（需认证），返回当前登录用户信息 `{ id, username, created_at }`。

#### Scenario: 已登录用户
- **WHEN** GET /api/auth/me 且携带有效 token
- **THEN** 返回当前用户信息

#### Scenario: 未认证
- **WHEN** GET /api/auth/me 且未携带 token 或 token 无效
- **THEN** 返回 401 错误

### Requirement: JWT 认证依赖
系统 SHALL 提供 FastAPI Depends 认证依赖 `get_current_user`，从请求的 `Authorization: Bearer <token>` 中解析 JWT，验证签名和过期时间，返回 User 实体。

#### Scenario: 有效 token
- **WHEN** 请求携带有效 JWT
- **THEN** 解析成功，注入 current_user 到请求上下文

#### Scenario: token 过期
- **WHEN** 请求携带已过期的 JWT
- **THEN** 返回 401 错误，提示"token 已过期"

#### Scenario: token 无效
- **WHEN** 请求携带格式错误或签名不匹配的 JWT
- **THEN** 返回 401 错误，提示"无效的认证凭据"

#### Scenario: 缺少 token
- **WHEN** 请求未携带 Authorization header
- **THEN** 返回 401 错误，提示"未提供认证凭据"

### Requirement: CLI 创建用户
系统 SHALL 提供 `python -m rag create-user --username <name> --password <pwd>` CLI 命令，创建新用户。

#### Scenario: 创建成功
- **WHEN** 执行 create-user 且用户名不存在
- **THEN** 创建用户并输出"用户 <name> 创建成功"

#### Scenario: 用户名已存在
- **WHEN** 执行 create-user 且用户名已存在
- **THEN** 输出错误"用户名已存在"并以非零退出码退出

### Requirement: 密码哈希
系统 SHALL 使用 bcrypt 对密码进行哈希存储，注册时哈希、登录时验证。

#### Scenario: 密码存储
- **WHEN** 创建用户
- **THEN** password 字段存储 bcrypt 哈希值，不存储明文

### Requirement: JWT 配置
系统 SHALL 从环境变量读取 JWT 密钥（`JWT_SECRET_KEY`）和过期时间（`JWT_EXPIRE_HOURS`，默认 24）。

#### Scenario: 未配置 JWT 密钥
- **WHEN** 启动时 JWT_SECRET_KEY 未设置
- **THEN** 使用默认密钥并输出警告（内部工具场景）
