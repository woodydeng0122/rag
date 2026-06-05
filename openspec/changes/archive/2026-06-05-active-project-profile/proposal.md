## Why

当前系统没有"激活项目"概念，用户每次操作文档必须先进入项目页再点进文档列表，缺乏全局上下文。需要一个全局激活项目机制，让用户在项目页设定当前工作项目后，Header 常驻显示项目名，文档列表独立为菜单入口并自动关联激活项目，减少导航层级。

## What Changes

- 新增 `profile` 数据库表（单例，id=1），仅存储 `active_project_id`
- 新增后端 Profile 实体、仓储接口、PostgreSQL 实现、API 路由（GET/PUT）
- 前端新增 `useActiveProjectStore`（Pinia），全局共享激活项目信息
- 项目页卡片增加"激活"操作，激活项目有视觉区分（左边缘色带 + 背景提升 + "当前项目"标签）
- Header 中间区域常驻显示激活项目名称（纯展示 + 点击跳转项目页）
- 侧边栏新增"文档管理"菜单入口
- **BREAKING**: 移除 `/projects/:id/documents` 路由，文档列表独立为 `/documents`，从 store 读取激活项目 ID
- 文档页无激活项目时显示引导空状态

## Capabilities

### New Capabilities
- `active-project-profile`: profile 表的 CRUD 及全局激活项目状态管理（后端 API + 前端 Store）
- `active-project-ui`: 项目页激活操作、激活卡片视觉区分、Header 常驻项目名、文档页独立入口及关联展示

### Modified Capabilities
<!-- 无现有 spec 需要修改 -->

## Impact

- **后端**: 新增 profile 领域实体、仓储、路由；Container 注册新依赖；新增数据库迁移脚本
- **前端**: 新增 Store、API 模块；修改 BasicLayout（Header + Sidebar）、ProjectList、DocumentList、路由配置
- **API**: 新增 `GET /api/profile`、`PUT /api/profile`；现有 API 不受影响
- **路由**: 移除 `/projects/:id/documents`，新增 `/documents`
