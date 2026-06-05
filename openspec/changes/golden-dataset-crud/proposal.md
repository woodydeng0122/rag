## Why

当前黄金数据集（golden_dataset）虽然在数据库中已有表结构，但缺乏完整的后端 CRUD 链路和前端管理页面。评测流程依赖前端手动传入 records 数组，无法持久化管理黄金数据，也无法追踪每条记录和项目级别的评测指标。需要补齐从 Domain → Infra → API → 前端的全链路 CRUD，并将评测结果持久化到项目和黄金记录上。

## What Changes

- 新增黄金数据集后端 CRUD 全链路：Domain 实体、Repository 端口、PG 实现、UseCase、API 路由
- 重构评测流程：前端只传 project_id + golden_ids，后端从 DB 加载数据并持久化评测结果
- project 表新增评测汇总字段（recall、mrr、可回答数、平均延迟、评测时间）
- golden_dataset 表新增评测结果字段（retrieved_chunk_ids、is_hit、hit_rank、evaluated_at）
- 新增项目级分块搜索 API，支持前端分块选择器按需加载
- 新增前端黄金数据集管理页面（表格 + 弹窗 + 批量操作）
- 侧边栏菜单新增「黄金数据集」入口
- 支持批量评测和批量删除，参考文档管理页的批量操作体验

## Capabilities

### New Capabilities
- `golden-dataset-crud`: 黄金数据集的增删改查全链路，包括后端 API 和前端表格页面
- `golden-dataset-evaluate`: 评测流程重构，支持从 DB 加载黄金数据、持久化评测结果到项目和记录级别
- `chunk-search`: 项目级分块搜索 API，支持前端分块选择器按关键词搜索和分页加载

### Modified Capabilities
- `project`: 项目实体和 API 新增评测汇总字段（eval_recall_at_10、eval_mrr、eval_answerable、eval_total、eval_latency_avg_ms、evaluated_at）

## Impact

- **后端 Domain**: Project 实体新增字段、GoldenRecord 实体重构（加 id/project_id/评测字段）、新增 GoldenDatasetRepositoryPort
- **后端 Infra**: 新增 PgGoldenDatasetRepository、PgProjectRepository 读写新字段、新增数据库 migration
- **后端 Application**: 新增 GoldenDatasetUseCase、EvaluateUseCase 重构
- **后端 API**: 新增 3 组路由（CRUD、评测、分块搜索）、新增/修改 schemas
- **前端**: 新增页面、API 层、路由、菜单项；依赖 activeProjectStore
- **数据库**: 2 个 migration（project 表加字段、golden_dataset 表加字段）
