## Why

黄金数据集检索已全部完成，但缺少项目级综合评估指标。当前只能逐条查看检索结果，无法从项目维度了解检索质量（如命中率、MRR、延迟分布），也无法对比不同嵌入模型或参数调整前后的效果变化。

## What Changes

- 新增项目评估统计 API：`POST /api/projects/{pid}/evaluation-stats`，用户输入 top_k（默认 10），后端基于已有检索结果过滤前 top_k 条目，计算 recall@{top_k} 和 MRR 等指标
- 新增 `project_evaluation` 表持久化评估结果，支持多次评估历史记录，便于对比优化效果
- 新增评估记录列表 API：`GET /api/projects/{pid}/evaluation-stats`，返回该项目所有评估历史
- 前端项目卡片新增"评估统计"操作按钮，点击后输入 top_k 触发评估
- 前端新增评估历史列表页，展示各次评估的指标对比，可视化优化效果

## Capabilities

### New Capabilities
- `project-evaluation-stats`: 项目级评估统计，计算 recall@{top_k}、MRR 等指标，持久化到独立表，提供列表查询和可视化

### Modified Capabilities
- `project-management`: 项目卡片操作栏新增评估统计入口

## Impact

- **后端 API**: 新增 2 个端点（触发评估、查询评估历史）
- **后端核心**: 新增 `ProjectEvaluationUseCase`，新增 `ProjectEvaluation` 实体和仓储
- **数据库**: 新增 `project_evaluation` 表
- **前端**: 项目卡片新增操作按钮，新增评估历史列表页（含指标对比可视化）
- **依赖**: 无新外部依赖
