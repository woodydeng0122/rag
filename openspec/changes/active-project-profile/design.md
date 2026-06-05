## Context

RAG 管理端采用 Clean Architecture 分层（Domain / Application / Infrastructure / API），前端为 Vue3 + Pinia + Ant Design Vue。当前系统有 Project 和 Document 两个核心实体，文档列表嵌套在项目路由下（`/projects/:id/documents`），没有全局"当前项目"概念，用户每次操作文档必须先导航到项目页再进入。

## Goals / Non-Goals

**Goals:**
- 建立全局激活项目机制，profile 表单例存储 active_project_id
- 前端全局 Store 共享激活项目信息，Header 常驻显示项目名
- 文档列表独立为一级菜单入口，自动关联激活项目
- 项目页激活操作有清晰视觉区分

**Non-Goals:**
- 不做多用户 profile（单用户管理端）
- 不做快速切换激活项目的下拉组件
- 不做 profile 表扩展（只存 active_project_id）
- 不做激活项目的权限控制

## Decisions

### D1: Profile 表单例方案 - 固定 id + UPSERT

**选择**: `id = 1` 固定主键，`INSERT ... ON CONFLICT (id) DO UPDATE` 实现 UPSERT

**备选方案**:
- A. 无表方案，active_project_id 存 localStorage - 简单但多设备不同步
- B. CHECK 约束限制单行 - 更严谨但语义与固定 id 等价

**理由**: 固定 id=1 + UPSERT 是最简单直接的方案，单用户管理端不需要更复杂的约束。ON CONFLICT 保证幂等性。

### D2: 激活项目视觉区分 - 左边缘色带

**选择**: 3px 左边缘色带（主题色 `#1677ff`）+ 背景微升（`#f0f7ff`）+ "当前项目" Tag

**备选方案**:
- A. 全边框包围 - 视觉噪音大
- B. 星标图标 - 语义混淆（收藏 vs 激活）
- C. 整体背景色变化 - 区分度不够

**理由**: 左边缘色带是经典的 active indicator 模式（VS Code、Notion），信息密度高但不吵。配合背景微升和标签，三层信息叠加保证区分度。

### D3: Header 激活项目名 - 纯展示 + 点击跳转

**选择**: Header 中间区域显示激活项目名，点击跳转项目页，不做下拉切换

**理由**: 项目页本身已有激活操作，路径足够短。下拉切换增加复杂度但收益有限。

### D4: 文档路由独立 - 移除嵌套路由

**选择**: 移除 `/projects/:id/documents`，新增 `/documents`，从 Store 读取 activeProjectId

**理由**: 文档页不再依赖 URL 中的项目 ID，而是从全局 Store 获取。路由更简洁，与激活项目机制一致。

### D5: Store 初始化时机 - App 启动时加载

**选择**: 在 BasicLayout 的 setup 阶段调用 `fetchActiveProject()`，确保所有子页面都能访问

**理由**: BasicLayout 是所有页面的父布局，在此初始化保证 Store 数据最早可用。

## Risks / Trade-offs

- [激活项目被删除] -> 后端 PUT /api/profile 时校验 project_id 存在性；前端监听项目列表变化，若激活项目被删则清空 Store 并提示
- [首次使用无激活项目] -> 文档页显示引导空状态，引导用户去项目页激活
- [路由变更 BREAKING] -> 旧 URL `/projects/:id/documents` 不再可用，需确认无外部依赖此路由
- [Store 与 API 状态不一致] -> 激活操作后立即更新 Store，失败则回滚；页面刷新时重新从 API 加载
