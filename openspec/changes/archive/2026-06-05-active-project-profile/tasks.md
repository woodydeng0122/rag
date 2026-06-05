## 1. 后端 - Profile 领域层

- [x] 1.1 创建 Profile 实体（`src/rag/domain/entities/profile.py`），包含 id 和 active_project_id 字段
- [x] 1.2 创建 ProfileRepositoryPort 接口（`src/rag/domain/ports/profile_repository.py`），定义 get() 和 upsert() 方法

## 2. 后端 - Profile 基础设施层

- [x] 2.1 创建数据库迁移脚本（`src/rag/infra/database/migrations/002_profile.sql`），建 profile 表并插入默认行
- [x] 2.2 创建 PgProfileRepository 实现（`src/rag/infra/repositories/pg_profile_repository.py`），实现 get() 和 upsert()

## 3. 后端 - Profile API 层

- [x] 3.1 创建 Profile API schemas（`src/rag/api/schemas/profile.py`），定义请求/响应模型
- [x] 3.2 创建 Profile 路由（`src/rag/api/routes/profile.py`），实现 GET /api/profile 和 PUT /api/profile
- [x] 3.3 在 Container 中注册 profile_repo 依赖
- [x] 3.4 在主路由中挂载 profile 路由

## 4. 前端 - Profile API 与 Store

- [x] 4.1 创建 Profile API 模块（`rag-web/src/api/profile.ts`）和类型定义
- [x] 4.2 创建 useActiveProjectStore（`rag-web/src/store/activeProject.ts`），包含 activeProjectId、activeProject、setActiveProject、fetchActiveProject

## 5. 前端 - 项目页激活功能

- [x] 5.1 修改 ProjectList.vue：卡片 actions 区域增加"激活"按钮，激活项目显示"当前项目" Tag 替代"激活"按钮
- [x] 5.2 修改 ProjectList.vue：激活项目卡片添加左边缘色带 + 背景色提升的样式
- [x] 5.3 修改 ProjectList.vue：删除项目后若为激活项目则清空 Store

## 6. 前端 - Header 与导航

- [x] 6.1 修改 BasicLayout.vue：Header 中间区域显示激活项目名称（有项目显示名称，无项目显示"未选择项目"），点击跳转项目页
- [x] 6.2 修改 BasicLayout.vue：Sidebar 增加"文档管理"菜单项（FileTextOutlined 图标，路由 /documents）
- [x] 6.3 修改 BasicLayout.vue：setup 阶段调用 fetchActiveProject() 初始化 Store

## 7. 前端 - 文档页独立

- [x] 7.1 修改路由配置：移除 /projects/:id/documents，新增 /documents 独立路由
- [x] 7.2 修改 DocumentList.vue：从 Store 读取 activeProjectId 替代 route.params.id
- [x] 7.3 修改 DocumentList.vue：无激活项目时显示引导空状态（提示去项目页激活 + 跳转链接）
- [x] 7.4 修改面包屑逻辑：文档页面包屑不再依赖项目名 query 参数
