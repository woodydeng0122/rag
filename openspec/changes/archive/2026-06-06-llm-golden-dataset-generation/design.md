## Context

黄金数据集 CRUD 和文件导入已完成（golden-crud / golden-import changes）。GoldenRecord 实体已有 query、ground_truth_chunks、reference_answer、metadata（含 type/difficulty/quality_score/supporting_quotes 等）字段。DashScopeLLM 已接入但仅用于 AskUseCase。

现有架构遵循 Clean Architecture：Domain（实体 + 端口）→ Infra（PG 实现）→ Application（用例）→ API（FastAPI 路由）。LLMPort 当前只有 `generate(prompt) -> str` 单方法。

项目使用 asyncio + FastAPI，已有后台协程模式（ProcessDocumentUseCase 使用 asyncio.create_task 处理文档）。

## Goals / Non-Goals

**Goals:**
- 实现两阶段 LLM 生成流水线：Phase 1 问题生成 → Phase 2 答案生成
- 支持按文档/选定 chunk 生成，串行执行
- 生成记录以 pending_review 状态入库，支持人工审批
- 追踪生成任务进度
- 分块详情展示关联黄金记录
- LLMPort 扩展支持结构化 JSON 输出

**Non-Goals:**
- 不做生成去重（重复生成不自动合并）
- 不做成本/配额控制
- 不做生成任务取消功能
- 不修改现有评测指标计算逻辑
- 不实现 Phase 1.5 语义去重（后续可迭代）
- 不实现 Groundedness 校验自动重试（仅标记，人工审核）

## Decisions

### 1. 两阶段生成策略

**决策**: Phase 1 从文档/chunk 生成问题（含类型、难度、可回答性、ground_truth_chunks 映射），Phase 2 为可回答问题生成参考答案

**理由**: 问题生成和答案生成关注点不同，分开可独立调优 prompt；Phase 1 可过滤 unanswerable 问题不进入 Phase 2，节省 LLM 调用；两阶段是 rag-golden-testset skill 推荐的最佳实践

**替代方案**: 单阶段一次性生成问题+答案 — prompt 复杂，输出不稳定，难以控制质量

### 2. 串行执行 + 文件粒度自适应

**决策**:
- 文件 ≤ 5000 字：整篇文档作为上下文，一次 LLM 调用生成所有问题，再映射回 chunk
- 文件 > 5000 字：3 chunk 为一轮，每轮一次 LLM 调用，ground_truth 直接确定
- Phase 2 逐问题串行生成答案

**理由**: 让模型集中注意力，避免上下文过长导致输出质量下降；3 chunk/轮是经验值，平衡上下文完整性和模型注意力

**替代方案**: 全部并行生成 — 模型注意力分散，输出质量不可控；全部逐 chunk — 小文件上下文不完整，问题碎片化

### 3. API 发完即返回 + 手动刷新

**决策**: POST /generate 创建任务后立即返回 task_id，后台 asyncio.create_task 执行生成，用户手动刷新查看进度

**理由**: 生成 50 条可能需要几分钟，同步等待会超时；项目已有 asyncio.create_task 模式（ProcessDocumentUseCase）；手动刷新比轮询更简单

**替代方案**: WebSocket 实时推送 — 实现复杂，当前场景不必要；前端轮询 — 增加复杂度，手动刷新够用

### 4. pending_review 状态入库

**决策**: LLM 生成的记录以 status=pending_review 入库，手动创建的记录 status=approved

**理由**: LLM 生成质量参差不齐，需要人工审核；直接入库方便用户查看和操作；审批是轻量操作（改 status 字段）

**替代方案**: 生成后不入库，审核后再入库 — 增加中间状态管理复杂度，用户无法预览

### 5. Phase 2 错误容忍

**决策**: Phase 2 单条答案生成失败不影响其他记录，已成功的保留入库，失败的在 task 中记录 failed 计数

**理由**: 串行执行中单条失败不应阻断整条流水线；用户可删除异常数据或手动编辑；重试逻辑增加复杂度，当前阶段不必要

**替代方案**: 失败自动重试 — 增加执行时间和复杂度；失败回滚所有 — 浪费已成功的 LLM 调用

### 6. LLMPort 扩展 generate_json

**决策**: LLMPort 新增 `generate_json(prompt: str, schema: dict | None = None) -> dict` 方法，内部做 JSON 解析和重试

**理由**: 生成流程需要结构化 JSON 输出（问题列表、答案对象）；纯 generate + 手动解析不可靠；schema 参数预留，当前 DashScope 实现用 prompt 工程保证 JSON 格式

**替代方案**: 在 UseCase 层做 JSON 解析 — 每个用例重复解析逻辑；不改 LLMPort 用 prompt + 正则提取 — 脆弱不可靠

### 7. 问题类型矩阵

**决策**: 采用 rag-golden-testset skill 的类型矩阵：factual 40%、procedural 25%、reasoning 15%、comparison 10%、unanswerable 10%

**理由**: 该矩阵覆盖了 RAG 评测的关键维度；factual 和 procedural 是最常见的用户查询类型；unanswerable 测试拒答能力，对评测有高区分度

### 8. 审批支持逐条 + 批量

**决策**: 支持单条 approve/reject 和批量 approve/reject，rejected 记录保留展示但提供删除操作

**理由**: 批量审批提高效率（一键通过全部 pending_review）；逐条审批保证精度；rejected 保留供参考，删除是独立操作

## Risks / Trade-offs

- **[LLM 输出不稳定]** JSON 格式可能解析失败 → generate_json 内置重试（最多 2 次），失败跳过该条记录
- **[生成耗时]** 大文档生成可能耗时较长 → 串行执行 + 任务进度追踪，用户可随时刷新查看
- **[DashScope 额度]** 批量生成可能耗尽免费额度 → 不做配额控制，用户自行管理
- **[ground_truth 映射准确性]** 整篇文档模式下 LLM 映射 chunk 可能不准 → prompt 中提供 chunk_id + heading 列表辅助映射；分批 chunk 模式下 ground_truth 直接确定
- **[generation_task 表膨胀]** 频繁生成产生大量任务记录 → 任务记录轻量，定期清理即可
