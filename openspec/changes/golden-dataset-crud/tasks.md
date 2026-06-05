## 1. 数据库 Migration

- [x] 1.1 创建 migration: golden_dataset 表新增 retrieved_chunk_ids TEXT[]、is_hit BOOLEAN、hit_rank INT、evaluated_at TIMESTAMPTZ 字段
- [x] 1.2 创建 migration: project 表新增 eval_recall_at_10 FLOAT、eval_mrr FLOAT、eval_answerable INT、eval_total INT、eval_latency_avg_ms FLOAT、evaluated_at TIMESTAMPTZ 字段

## 2. Domain 层

- [x] 2.1 重构 GoldenRecord 实体：新增 id、project_id、retrieved_chunk_ids、is_hit、hit_rank、evaluated_at、created_at 字段
- [x] 2.2 新增 GoldenDatasetRepositoryPort 端口：save、get_by_id、list_by_project、update、delete 方法
- [x] 2.3 更新 Project 实体：新增评测汇总字段

## 3. Infra 层

- [x] 3.1 实现 PgGoldenDatasetRepository：完整的 CRUD + list_by_project
- [x] 3.2 更新 PgProjectRepository：读写评测汇总字段
- [x] 3.3 实现 PgChunkRepository.list_by_project：按项目查询所有分块（含搜索）
- [x] 3.4 更新 ChunkRepositoryPort：新增 list_by_project 和 search_by_project 方法

## 4. Application 层

- [x] 4.1 新增 GoldenDatasetUseCase：CRUD 用例
- [x] 4.2 重构 EvaluateUseCase：支持从 DB 按 project_id + golden_ids 加载，评测结果持久化到记录和项目
- [x] 4.3 更新 Container：注册 GoldenDatasetUseCase 和新依赖

## 5. API 层

- [x] 5.1 新增 golden_dataset schemas：CreateGoldenDatasetRequest、UpdateGoldenDatasetRequest、GoldenDatasetResponse
- [x] 5.2 新增 golden_dataset 路由：CRUD 四个端点
- [x] 5.3 重构 evaluate 路由：改为 POST /api/projects/{pid}/evaluate，接收 golden_ids
- [x] 5.4 更新 evaluate schemas：新增 EvaluateByProjectRequest
- [x] 5.5 新增 chunks/search 路由：GET /api/projects/{pid}/chunks/search
- [x] 5.6 更新 project schemas：响应新增评测汇总字段
- [x] 5.7 注册新路由到 app.py

## 6. 前端 API 层

- [x] 6.1 新增 api/model/goldenDatasetModel.ts：GoldenDatasetItem、CreateGoldenDatasetParams 等类型
- [x] 6.2 新增 api/goldenDataset.ts：CRUD + 评测 API 调用
- [x] 6.3 新增 api/chunk.ts：分块搜索 API 调用
- [x] 6.4 更新 api/model/projectModel.ts：ProjectItem 新增评测字段

## 7. 前端页面

- [x] 7.1 新增 GoldenDataset.vue：表格页面（列定义、数据加载、分页、行选择）
- [x] 7.2 实现新增/编辑弹窗：查询文本、分块选择器、参考答案
- [x] 7.3 实现分块选择器组件：搜索+分页加载+勾选+已选回显
- [x] 7.4 实现批量操作：批量评测、批量删除（参考 DocumentList）
- [x] 7.5 实现单条操作：编辑、评测、删除
- [x] 7.6 处理未选择项目状态：显示提示信息

## 8. 前端路由与菜单

- [x] 8.1 更新 router/index.ts：新增 /golden-dataset 路由
- [x] 8.2 更新 BasicLayout.vue：侧边栏新增"黄金数据集"菜单项（TrophyOutlined 图标）
- [x] 8.3 更新面包屑：支持 /golden-dataset 路径
