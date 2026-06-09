## 1. 数据库迁移

- [x] 1.1 新建 `010_project_evaluation.sql`，创建 `project_evaluation` 表（id, project_id, top_k, golden_total, golden_retrieved, recall_at_k, mrr, hit_rate, full_hit_count, zero_hit_count, avg_latency_ms, avg_embed_latency_ms, avg_search_latency_ms, embed_model_name, created_at）
- [x] 1.2 创建索引 `idx_project_evaluation_project_id ON project_evaluation(project_id)`

## 2. 领域层

- [x] 2.1 新建 `ProjectEvaluation` 实体（domain/entities/project_evaluation.py）
- [x] 2.2 新建 `ProjectEvaluationRepositoryPort` 端口（domain/ports/project_evaluation_repository.py），定义 `save()` 和 `list_by_project()` 方法

## 3. 基础设施层

- [x] 3.1 新建 `PgProjectEvaluationRepository` 实现（infra/repositories/pg_project_evaluation_repository.py），实现 `save()` 和 `list_by_project()`
- [x] 3.2 在 `GoldenRetrievalRepositoryPort` 新增 `list_by_project_with_items()` 方法，支持按项目批量加载检索结果和 items
- [x] 3.3 在 `PgGoldenRetrievalRepository` 实现 `list_by_project_with_items()`

## 4. 应用层

- [x] 4.1 新建 `ProjectEvaluationUseCase`（application/usecases/project_evaluation.py），实现 `execute(project_id, top_k)` 方法
- [x] 4.2 实现 recall@{top_k} 计算：按 rank <= top_k 过滤 items，计算每条记录的 recall 后取平均
- [x] 4.3 实现 MRR 计算：找首个 GT 命中的 rank，计算 rr 后取平均
- [x] 4.4 实现 hit_rate、full_hit_count、zero_hit_count 计算
- [x] 4.5 实现延迟指标聚合（avg_latency_ms、avg_embed_latency_ms、avg_search_latency_ms）
- [x] 4.6 将评估结果持久化到 `project_evaluation` 表
- [x] 4.7 实现 `list_evaluations(project_id)` 方法，返回评估历史

## 5. API 层

- [x] 5.1 新建 `EvaluationStatsRequest` Schema（top_k: int = 10, ge=1, le=100）
- [x] 5.2 新建 `EvaluationStatsResponse` Schema，包含所有评估指标字段
- [x] 5.3 新增 `POST /api/projects/{pid}/evaluation-stats` 路由
- [x] 5.4 新增 `GET /api/projects/{pid}/evaluation-stats` 路由
- [x] 5.5 `bootstrap/container.py` 注册 `ProjectEvaluationUseCase` 依赖

## 6. 前端

- [x] 6.1 `projectModel.ts` 新增 `EvaluationStatsResult` 类型定义
- [x] 6.2 `project.ts` API 新增 `triggerEvaluation` 和 `getEvaluationHistory` 接口
- [x] 6.3 `ProjectList.vue` 项目卡片 actions 新增 BarChartOutlined 评估统计按钮
- [x] 6.4 `ProjectList.vue` 新增评估统计 Drawer 组件（top_k 输入 + 评估结果展示）
- [x] 6.5 新增评估历史列表页 `EvaluationHistory.vue`（路由 `/projects/:id/evaluation`）
- [x] 6.6 评估历史页：`a-table` 展示评估记录列表
- [x] 6.7 评估历史页：折线图展示 recall@k 和 MRR 趋势
