## 1. 数据库 Migration

- [x] 1.1 创建 migration: golden_dataset 表新增 status VARCHAR(32) NOT NULL DEFAULT 'approved' 列，新增索引 idx_golden_dataset_status
- [x] 1.2 创建 migration: 新建 generation_task 表（id, project_id, status, total, completed, failed, document_ids, chunk_ids, config, error_message, created_at, finished_at），新增索引 idx_generation_task_project_id

## 2. Domain 层

- [x] 2.1 更新 GoldenRecord 实体：新增 status: str = "approved" 字段
- [x] 2.2 新增 GenerationTask 实体：id, project_id, status, total, completed, failed, document_ids, chunk_ids, config, error_message, created_at, finished_at
- [x] 2.3 新增 GenerateConfig 值对象：per_chunk, question_types, difficulty, user_persona, chunk_batch_size, file_char_threshold
- [x] 2.4 扩展 LLMPort：新增 generate_json(prompt, schema) 抽象方法
- [x] 2.5 新增 GenerationTaskRepositoryPort 端口：save, get_by_id, list_by_project, update
- [x] 2.6 扩展 GoldenDatasetRepositoryPort：新增 list_by_project_and_status, update_status, batch_update_status, list_by_chunk_id

## 3. Infra 层

- [x] 3.1 实现 DashScopeLLM.generate_json：JSON 提取（直接解析 → 代码块提取 → 大括号提取）+ 重试（最多 2 次）+ schema prompt 增强
- [x] 3.2 实现 PgGenerationTaskRepository：save, get_by_id, list_by_project, update
- [x] 3.3 更新 PgGoldenDatasetRepository：save/get/update 读写 status 字段，新增 list_by_project_and_status, update_status, batch_update_status, list_by_chunk_id 方法

## 4. Application 层

- [x] 4.1 新增 GenerateGoldenUseCase：两阶段串行生成核心逻辑
  - 加载目标 chunks（按 document_ids 或 chunk_ids）
  - 创建 GenerationTask
  - asyncio.create_task 启动后台协程
  - 后台协程：整篇文档模式 / 分批 chunk 模式
  - Phase 1 prompt 构建（整篇 + 分批两种）
  - Phase 2 prompt 构建
  - 质量评分计算
  - 逐条入库（status=pending_review）
  - 异常容忍 + task 进度更新
- [x] 4.2 扩展 GoldenDatasetUseCase：新增 approve, reject, batch_approve, batch_reject 方法
- [x] 4.3 更新 Container：注册 GenerateGoldenUseCase + GenerationTaskRepositoryPort

## 5. API 层

- [x] 5.1 新增 schemas：GenerateGoldenRequest, GenerateGoldenResponse, GenerationTaskResponse, BatchStatusUpdateRequest, BatchStatusUpdateResponse
- [x] 5.2 更新 GoldenDatasetResponse：新增 status 字段
- [x] 5.3 新增 POST /api/projects/{pid}/golden-datasets/generate 路由
- [x] 5.4 新增 GET /api/projects/{pid}/generation-tasks 路由
- [x] 5.5 新增 GET /api/projects/{pid}/generation-tasks/{tid} 路由
- [x] 5.6 新增 POST /api/projects/{pid}/golden-datasets/batch-approve 路由
- [x] 5.7 新增 POST /api/projects/{pid}/golden-datasets/batch-reject 路由
- [x] 5.8 扩展 PATCH /api/projects/{pid}/golden-datasets/{rid}：支持 status 字段更新
- [x] 5.9 扩展 GET /api/projects/{pid}/golden-datasets：支持 ?status= 过滤参数
- [x] 5.10 新增 GET /api/projects/{pid}/chunks/{cid}/golden-records 路由
- [x] 5.11 注册新路由到 app.py（路由已在现有文件中，无需额外注册）

## 6. 前端 API 层

- [x] 6.1 新增 api/model/generationTaskModel.ts：GenerationTaskItem, GenerateGoldenParams, GenerateConfig 类型
- [x] 6.2 新增 api/generationTask.ts：generateGolden, getGenerationTasks, getGenerationTask API 调用
- [x] 6.3 更新 api/model/goldenDatasetModel.ts：GoldenDatasetItem 新增 status 字段，新增 BatchStatusUpdateParams 类型
- [x] 6.4 更新 api/goldenDataset.ts：新增 batchApprove, batchReject API 调用
- [x] 6.5 更新 api/chunk.ts：新增 getChunkGoldenRecords API 调用

## 7. 前端页面 — GoldenDataset.vue

- [x] 7.1 工具栏新增"LLM 生成"按钮
- [x] 7.2 工具栏新增状态筛选下拉（全部 / 待审核 / 已审批 / 已拒绝）
- [x] 7.3 工具栏新增"批量审批"和"批量拒绝"按钮
- [x] 7.4 表格新增状态列（🟡待审核 / 🟢已通过 / 🔴已拒绝）
- [x] 7.5 操作列新增审批/拒绝按钮（仅 pending_review 状态显示）
- [x] 7.6 实现生成配置弹窗：文档选择器 + 生成参数配置
- [x] 7.7 实现生成结果刷新：手动刷新查看进度
- [x] 7.8 rejected 记录灰色展示

## 8. 前端页面 — 分块详情

- [x] 8.1 分块详情弹窗新增"关联黄金记录"Tab
- [x] 8.2 展示关联记录列表：query + 状态 + 类型 + 质量评分
- [x] 8.3 空状态处理
