## Context

黄金数据集检索已完成，每条 golden_record 对应一条 golden_retrieval（含 latency_ms、embed_latency_ms、search_latency_ms）和若干 golden_retrieval_item（含 chunk_id、score、rank）。当前只能逐条查看检索结果和 GT 命中情况，缺少项目维度的综合评估指标。

用户需要：
1. 输入 top_k 参数（默认 10），对已有检索结果按 top_k 截断后重新计算指标
2. 项目级综合指标：recall@{top_k}、MRR、命中率、延迟分布等
3. 评估结果持久化到独立表，支持多次评估历史对比
4. 前端可视化展示优化效果

## Goals / Non-Goals

**Goals:**
- 用户输入 top_k，基于已有检索结果（golden_retrieval + golden_retrieval_item）计算项目级指标
- recall@{top_k}：在 top_k 截断下的召回率
- MRR：平均倒数排名
- 评估结果持久化到 `project_evaluation` 新表，每次评估生成一条记录
- 提供评估历史列表 API，支持对比不同次评估的指标
- 前端项目卡片新增"评估统计"操作按钮
- 前端新增评估历史列表页，展示指标趋势和对比

**Non-Goals:**
- 不重新执行检索（基于已有检索结果计算）
- 不修改 project 表结构（评估数据独立存储）
- 不做评估结果自动触发（用户手动点击）
- 不做跨项目对比

## Decisions

### D1: 基于已有检索结果计算，不重新检索

**选择**: 从 `golden_retrieval` + `golden_retrieval_item` 表读取已有数据，按 top_k 截断后计算指标

**理由**:
- 检索已全部完成，重新检索耗时且无意义
- top_k 截断只需过滤 `rank <= top_k` 的 item，纯内存计算
- 计算速度快，用户体验好

### D2: 独立 `project_evaluation` 表，不修改 project 表

**选择**: 新建 `project_evaluation` 表存储评估结果，每次评估一条记录

**理由**:
- 评估是快照，同一项目可能多次评估（换模型后重新检索再评估）
- project 表保持简洁，评估历史可追溯
- 便于前端展示时间线对比

**表结构**:
```sql
CREATE TABLE project_evaluation (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES project(id) ON DELETE CASCADE,
    top_k INT NOT NULL,
    golden_total INT NOT NULL,          -- 黄金记录总数
    golden_retrieved INT NOT NULL,      -- 已检索数
    recall_at_k FLOAT NOT NULL,         -- recall@{top_k}
    mrr FLOAT NOT NULL,                 -- MRR
    hit_rate FLOAT NOT NULL,            -- 加权平均命中率
    full_hit_count INT NOT NULL,        -- 完全命中数
    zero_hit_count INT NOT NULL,        -- 零命中数
    avg_latency_ms FLOAT NOT NULL,      -- 平均总延迟
    avg_embed_latency_ms FLOAT NOT NULL,-- 平均嵌入延迟
    avg_search_latency_ms FLOAT NOT NULL,-- 平均检索延迟
    embed_model_name VARCHAR(255) NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### D3: 指标计算公式

**recall@{top_k}**:
```
对每条 golden_record:
  retrieved_in_topk = {item.chunk_id for item in items if item.rank <= top_k}
  recall_i = |retrieved_in_topk ∩ ground_truth_chunks| / |ground_truth_chunks|

recall@{top_k} = mean(recall_i for all golden_records with retrieval)
```

**MRR**:
```
对每条 golden_record:
  first_gt_rank = min(item.rank for item in items if item.is_ground_truth) 或 ∞
  rr_i = 1 / first_gt_rank

MRR = mean(rr_i for all golden_records with retrieval)
```

**hit_rate**:
```
hit_rate = sum(hit_count) / sum(gt_total)
其中 hit_count = |retrieved_in_topk ∩ ground_truth_chunks|
```

### D4: API 设计

```
POST   /api/projects/{pid}/evaluation-stats        → 触发评估，body: { top_k: 10 }
GET    /api/projects/{pid}/evaluation-stats         → 查询评估历史列表
```

RESTful 风格，`evaluation-stats` 作为项目的子资源。

### D5: 前端交互

**项目卡片**: actions 栏新增 BarChartOutlined 图标按钮，点击后弹出 Drawer：
- 顶部输入 top_k（默认 10），点击"开始评估"
- 评估完成后在 Drawer 内展示当前结果
- 底部链接"查看评估历史"跳转列表页

**评估历史列表页**: 新增路由 `/projects/:id/evaluation`：
- 表格展示各次评估记录（时间、top_k、recall、MRR、命中率、延迟）
- 折线图展示 recall@k 和 MRR 随时间变化趋势
- 使用 Ant Design Vue 的 `a-table` + `a-statistic` + 简易折线图

### D6: 依赖方向

```
project_evaluation (新实体)
    ↓
ProjectEvaluationRepositoryPort (新端口)
    ↓
ProjectEvaluationUseCase (新用例)
    ↓
routes/project.py (新增路由)
```

符合 clean-architecture 依赖规则。

## Risks / Trade-offs

- **[top_k > max_k]** → 用户输入的 top_k 可能大于检索时的 max_k，此时 recall@{top_k} = recall@{max_k}（因为检索结果最多 max_k 条）。前端需提示"top_k 超过检索 max_k 时，实际按 max_k 计算"。
- **[未检索的记录]** → 部分 golden_record 可能没有检索结果，评估时跳过这些记录，`golden_retrieved` 字段反映实际参与评估的记录数。
- **[评估计算量]** → 项目级评估需要遍历所有 golden_retrieval + items，数据量大时可能较慢。但这是读操作，且 top_k 截断在 SQL 层完成（`WHERE rank <= $1`），性能可控。
