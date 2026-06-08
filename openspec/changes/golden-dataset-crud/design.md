## Context

当前 RAG 系统已有 `golden` 数据库表，但后端仅实现了评测用例（EvaluateUseCase），且评测时黄金数据由前端在请求体中传入，无法持久化管理。前端没有黄金数据集管理页面。

现有架构遵循 Clean Architecture：Domain（实体 + 端口）→ Infra（PG 实现）→ Application（用例）→ API（FastAPI 路由）。前端使用 Vue 3 + Ant Design Vue + Pinia，已有 `activeProjectStore` 管理当前激活项目。

项目已有成熟的 CRUD 模式可参考：ProjectRepositoryPort → PgProjectRepository → API 路由 → 前端表格/弹窗。

## Goals / Non-Goals

**Goals:**
- 补齐黄金数据集后端 CRUD 全链路（Domain → Infra → Application → API）
- 重构评测流程：后端从 DB 加载黄金数据，持久化评测结果到项目和记录级别
- 新增前端黄金数据集管理页面，支持表格展示、弹窗编辑、批量操作
- 分块选择器支持搜索+分页加载，适配大数据量场景

**Non-Goals:**
- 不重构现有评测指标计算逻辑（recall_at_k、MRR）
- 不修改前端项目列表/文档管理页面
- 不做评测结果历史趋势分析
- 不支持跨项目评测

## Decisions

### 1. 黄金数据集归属项目级

**决策**: 黄金数据集按 project_id 关联，页面依赖 activeProjectStore 获取当前项目

**理由**: DB 表已有 project_id 外键；与文档管理页导航模式一致；评测时自然限定在项目范围内

**替代方案**: 全局独立页面 — 违反现有数据模型，且评测需要项目上下文

### 2. 评测结果持久化到两个层级

**决策**:
- `golden` 表记录每条记录的评测细节（retrieved_chunk_ids、is_hit、hit_rank、evaluated_at）
- `project` 表记录项目级汇总（eval_recall_at_10、eval_mrr、eval_answerable、eval_total、eval_latency_avg_ms、evaluated_at）

**理由**: 项目级汇总便于 Dashboard 展示；记录级细节便于定位未命中查询，优化检索策略

**替代方案**: 独立评测结果表 — 增加关联复杂度，当前场景下汇总字段直接放 project 更简洁

### 3. 评测 API 改为 project_id + golden_ids 驱动

**决策**: `POST /api/projects/{pid}/evaluate`，body 为 `{ golden_ids, k_list }`，后端从 DB 加载并持久化

**理由**: 前端不再需要传完整 records 数组；评测结果可持久化回写；支持批量评测

**替代方案**: 保留前端传 records — 无法持久化评测结果，与 CRUD 数据割裂

### 4. 分块选择器采用搜索+分页模式

**决策**: 新增 `GET /api/projects/{pid}/chunks/search?q=xxx&limit=20`，前端按需搜索加载

**理由**: 项目下可能有数百到数千分块，一次性全加载性能差；搜索模式用户体验更好

**替代方案**: 一次性全加载 + 前端虚拟滚动 — 数据量大时初始加载慢，内存占用高

### 5. 前端表格模式 + 弹窗编辑

**决策**: 参照 DocumentList 的表格模式，弹窗编辑新增/修改

**理由**: 黄金数据集字段结构化（query、chunks、answer），表格适合展示和批量选择；弹窗适合编辑复杂内容

### 6. 批量操作参考文档管理页

**决策**: 表格行选择 + 工具栏批量按钮（批量评测、批量删除），数量多时逐条执行并汇总结果

**理由**: 与现有交互模式一致；批量评测本质是逐条检索，需要逐条反馈进度

## Risks / Trade-offs

- **[评测耗时]** 批量评测大量记录时可能耗时较长 → 前端显示 loading 状态，后端逐条执行不超时
- **[分块搜索性能]** 大项目分块搜索可能慢 → 加 LIMIT 限制，前端防抖搜索
- **[评测数据一致性]** 部分记录评测成功部分失败 → 已成功的持久化，失败的在响应中标记，前端提示部分成功
- **[project 表字段膨胀]** 评测汇总字段增加 project 表宽度 → 字段有限（6个），可接受；未来可考虑独立表
