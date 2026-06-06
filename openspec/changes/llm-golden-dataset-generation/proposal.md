## Why

当前黄金数据集完全依赖人工创建或文件导入，缺少 LLM 自动生成能力。已有 DashScopeLLM 基础设施但仅用于 AskUseCase，未复用到数据集生成。需要建立两阶段 LLM 生成流水线（问题生成 → 答案生成），以待审核状态入库，支持人工审批，降低数据准备成本。

## What Changes

- 新增两阶段 LLM 生成流水线：Phase 1 从文档/chunk 生成问题（含类型、难度、可回答性、ground_truth 映射），Phase 2 为可回答问题生成参考答案（含 supporting_quotes、quality_score、groundedness）
- 新增 GenerationTask 实体和仓储，追踪生成任务进度（running/completed/failed）
- GoldenRecord 新增 status 字段（pending_review/approved/rejected），LLM 生成记录默认 pending_review
- LLMPort 扩展 generate_json 方法，支持结构化 JSON 输出
- 新增审批操作：逐条审批 + 批量审批（approve/reject），rejected 记录保留展示但提供删除
- 新增分块关联黄金记录查询：chunk 详情页展示关联的黄金数据集
- 串行执行策略：文件 ≤5千字整篇处理，>5千字 3 chunk/轮，让模型集中注意力
- API 发完任务即返回，用户手动刷新查看进度

## Capabilities

### New Capabilities
- `golden-dataset-generation`: LLM 驱动的黄金数据集两阶段生成，支持按文档/选定 chunk 生成，串行执行，异步任务追踪
- `golden-dataset-review`: 黄金数据集审批流程，支持逐条和批量 approve/reject，状态筛选
- `chunk-golden-records`: 分块关联黄金记录查询，chunk 详情页展示关联数据
- `llm-json-output`: LLMPort 扩展 generate_json 方法，支持结构化 JSON 输出和解析重试

### Modified Capabilities
- `golden-dataset-crud`: GoldenRecord 实体新增 status 字段，API 支持 status 过滤和更新

## Impact

- **后端 Domain**: GoldenRecord 新增 status 字段；新增 GenerationTask 实体；LLMPort 新增 generate_json 方法；新增 GenerationTaskRepositoryPort；GoldenDatasetRepositoryPort 新增查询方法
- **后端 Infra**: DashScopeLLM 实现 generate_json；新增 PgGenerationTaskRepository；PgGoldenDatasetRepository 增加查询方法；新增 DB migration
- **后端 Application**: 新增 GenerateGoldenUseCase（两阶段串行生成 + 后台协程）；GoldenDatasetUseCase 扩展审批方法
- **后端 API**: 新增生成、任务查询、审批、分块关联黄金记录接口
- **前端**: GoldenDataset.vue 新增生成按钮、状态筛选、审批操作；分块详情新增关联黄金记录 Tab
- **数据库**: golden_dataset 表加 status 列；新建 generation_task 表
