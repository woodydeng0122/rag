## Purpose

项目级评估统计功能 - 基于已有检索结果计算 recall@{top_k}、MRR 等综合指标，持久化评估历史，支持多次评估对比和可视化优化效果。

## Requirements

### Requirement: Trigger project evaluation with top_k
系统 SHALL 提供项目评估统计 API，用户输入 top_k（默认 10），基于已有检索结果计算项目级综合指标。重排评估需校验项目是否配置了重排模型。

#### Scenario: 正常粗排评估
- **WHEN** 请求 `POST /api/projects/{pid}/evaluation-stats`，body 为 `{ top_k: 10, category: "recall" }`
- **THEN** 后端从 golden_retrieval + golden_retrieval_item 表加载该项目的检索结果，按 rank <= top_k 过滤，计算 recall@{top_k}、MRR、hit_rate、full_hit_count、zero_hit_count、avg_latency_ms、avg_embed_latency_ms、avg_search_latency_ms，持久化到 project_evaluation 表，返回评估结果

#### Scenario: 正常重排评估
- **WHEN** 请求 `POST /api/projects/{pid}/evaluation-stats`，body 为 `{ top_k: 10, category: "rerank" }`，且项目已配置重排模型
- **THEN** 后端从 golden_rerank + golden_rerank_item 表加载该项目的重排结果，按 rerank_rank <= top_k 过滤，计算指标并持久化

#### Scenario: 重排评估但项目未配置重排模型
- **WHEN** 请求 `POST /api/projects/{pid}/evaluation-stats`，body 为 `{ category: "rerank" }`，但项目 `rerank_model_id` 为 NULL
- **THEN** 返回 400 错误，提示"项目未配置重排模型"

#### Scenario: 项目无重排结果
- **WHEN** 请求 `POST /api/projects/{pid}/evaluation-stats`，body 为 `{ category: "rerank" }`，项目已配置重排模型但无重排结果
- **THEN** 返回 400 错误，提示"项目无重排结果，请先执行重排"

#### Scenario: top_k 默认值
- **WHEN** 请求 `POST /api/projects/{pid}/evaluation-stats`，body 为 `{}`
- **THEN** top_k 默认为 10

#### Scenario: top_k 超过 max_k
- **WHEN** 用户输入 top_k=20，但检索时的 max_k=10
- **THEN** 按 max_k=10 计算（检索结果最多 10 条），评估结果中 top_k 记录用户输入值

#### Scenario: 项目无检索结果
- **WHEN** 项目下没有任何 golden_retrieval 记录
- **THEN** 返回 400 错误，提示"项目无检索结果，请先执行检索"

### Requirement: Recall@{top_k} calculation
系统 SHALL 按 top_k 截断检索结果后计算 recall@{top_k}。

#### Scenario: 计算 recall
- **WHEN** 对某条 golden_record 计算 recall@{top_k}
- **THEN** 取 rank <= top_k 的 retrieval items，计算 `|retrieved_chunks ∩ ground_truth_chunks| / |ground_truth_chunks|`，所有记录取算术平均

#### Scenario: ground_truth_chunks 为空
- **WHEN** 某条 golden_record 的 ground_truth_chunks 为空
- **THEN** 跳过该记录，不参与 recall 计算

### Requirement: MRR calculation
系统 SHALL 计算 MRR（Mean Reciprocal Rank）。

#### Scenario: 计算 MRR
- **WHEN** 对某条 golden_record 计算 MRR
- **THEN** 找到 rank <= top_k 的 items 中首个 is_ground_truth=True 的 rank 值，rr = 1/rank；若无命中则 rr=0；所有记录取算术平均

### Requirement: Persist evaluation to project_evaluation table
系统 SHALL 将评估结果持久化到 `project_evaluation` 表，每次评估生成一条记录。

#### Scenario: 评估结果持久化
- **WHEN** 评估计算完成
- **THEN** 写入 project_evaluation 表，包含 project_id、top_k、golden_total、golden_retrieved、recall_at_k、mrr、hit_rate、full_hit_count、zero_hit_count、avg_latency_ms、avg_embed_latency_ms、avg_search_latency_ms、embed_model_name、created_at

#### Scenario: 多次评估
- **WHEN** 同一项目多次触发评估
- **THEN** 每次生成新记录，保留历史，不覆盖

### Requirement: List evaluation history
系统 SHALL 提供评估历史列表 API。

#### Scenario: 查询评估历史
- **WHEN** 请求 `GET /api/projects/{pid}/evaluation-stats`
- **THEN** 返回该项目所有评估记录，按 created_at 降序排列

### Requirement: Project evaluation database migration
系统 SHALL 提供 migration 新建 project_evaluation 表。

#### Scenario: Migration 执行
- **WHEN** 执行数据库 migration
- **THEN** 创建 project_evaluation 表，包含 id、project_id、top_k、golden_total、golden_retrieved、recall_at_k、mrr、hit_rate、full_hit_count、zero_hit_count、avg_latency_ms、avg_embed_latency_ms、avg_search_latency_ms、embed_model_name、created_at 字段

### Requirement: Project card evaluation action
前端项目卡片 SHALL 新增"评估统计"操作按钮，点击后输入 top_k 触发评估。

#### Scenario: 点击评估按钮
- **WHEN** 用户点击项目卡片的评估统计按钮
- **THEN** 弹出 Drawer，显示 top_k 输入框（默认 10）和"开始评估"按钮

#### Scenario: 评估完成展示
- **WHEN** 评估计算完成
- **THEN** Drawer 内展示评估结果：recall@{top_k}、MRR、命中率、完全命中/零命中、延迟分布

### Requirement: Evaluation history list page
前端 SHALL 新增评估历史独立页面（侧边栏导航入口），展示各次评估指标对比和趋势。

#### Scenario: 侧边栏导航入口
- **WHEN** 侧边栏渲染
- **THEN** 显示"评估历史"菜单项，点击跳转到当前激活项目的评估历史页

#### Scenario: 访问评估历史页
- **WHEN** 用户点击侧边栏"评估历史"或从 Drawer 点击"查看评估历史"
- **THEN** 跳转到 `/projects/:id/evaluation` 页面，展示评估记录表格和趋势折线图

#### Scenario: 面包屑导航
- **WHEN** 用户访问评估历史页
- **THEN** 面包屑显示"项目管理 > 评估历史"

#### Scenario: 指标趋势可视化
- **WHEN** 评估历史 >= 2 条
- **THEN** 折线图展示 recall@k 和 MRR 随时间变化趋势
