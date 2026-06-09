## Context

当前 RAG 系统已有完整的检索链路：`CosineRetriever` → `BaseRetrieveUseCase._retrieve_chunks()` → `POST /api/projects/{id}/retrievals`。黄金数据集页面（Golden.vue）已有 CRUD、审批、导入功能，但缺少检索验证能力。

现有架构遵循 Clean Architecture：Domain（实体 + 端口）→ Infra（PG 实现）→ Application（用例）→ API（FastAPI 路由）。前端使用 Vue 3 + Ant Design Vue + Pinia。

## Goals / Non-Goals

**Goals:**
- 为每条黄金记录提供语义检索功能，用 record.query 调用已有 RetrieverPort
- 检索结果持久化到独立表（golden_retrieval + golden_retrieval_item），支持覆盖重检
- 记录检索指标：latency_ms、max_k、embed_model_name、created_at
- 后端计算 GT 命中标记并 join chunk 内容，一次请求返回完整数据
- 前端表格新增检索列，Modal 交互输入 max_k 并展示检索结果

**Non-Goals:**
- 不保留检索历史（覆盖模式）
- 不做批量检索
- 不修改现有检索链路（CosineRetriever、RetrieveUseCase）
- 不做检索结果趋势分析

## Decisions

### 1. 独立表存储检索结果（方案 B）

**决策**: 新增 `golden_retrieval` + `golden_retrieval_item` 两张表，与 `golden` 表通过 golden_id 关联

**理由**: 独立表结构清晰，检索结果与黄金记录解耦；golden_retrieval_item 存储每个 chunk 的 score/rank，便于后续分析；JSON 字段不好查询和扩展

**替代方案**: 在 GoldenRecord 上加 JSON 字段 — 查询不便，结构不清晰

### 2. 检索指标：latency_ms、max_k、embed_model_name、created_at

**决策**: 不存 top_k，用 max_k 替代（语义更清晰：检索时请求的最大数量，实际返回可能少于 max_k）

**理由**: top_k 可从 max_k 截取推导；embed_model_name 记录使用的模型，方便对比不同模型效果

### 3. 覆盖模式，不保留历史

**决策**: 重新检索时删除旧的 golden_retrieval 及其 items，写入新结果

**理由**: 当前场景只需最新检索结果；保留历史增加复杂度，暂无需求

### 4. 后端 join chunk 内容 + GT 命中标记

**决策**: GET retrieval API 返回时后端 join chunk 表获取 content/heading/source_file，并计算 is_ground_truth 标记

**理由**: 一次请求返回完整数据，前端无需二次调用；GT 命中需要后端对比 ground_truth_chunks 与检索结果，前端做需要额外数据

### 5. API 设计遵循 RESTful

**决策**:
- `POST /api/projects/{project_id}/golden/{record_id}/retrieval` — 触发检索（创建/覆盖资源）
- `GET /api/projects/{project_id}/golden/{record_id}/retrieval` — 获取检索结果

**理由**: retrieval 是 golden record 的子资源，POST 触发创建，GET 获取；符合 RESTful 嵌套资源模式

### 6. 前端交互：Modal + max_k 默认 10

**决策**: 点击检索按钮弹出 Modal，显示 query（只读）和 max_k 输入框（默认 10），确认后执行检索

**理由**: Modal 比 Popover 空间更大，适合展示检索结果列表；max_k 默认 10 是合理默认值

## Data Model

```
┌─────────────────────────────────────────────────────────────────┐
│  golden (已有)                                                   │
│  id UUID PK, project_id UUID FK, query TEXT                     │
│  ground_truth_chunks TEXT[], reference_answer TEXT               │
│  status VARCHAR, metadata JSONB, created_at TIMESTAMPTZ         │
└──────────────────────────┬──────────────────────────────────────┘
                           │ 1:1 (覆盖模式)
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  golden_retrieval                                                │
│  id UUID PK DEFAULT gen_random_uuid()                           │
│  golden_id UUID FK → golden(id) ON DELETE CASCADE               │
│  max_k INT NOT NULL                                             │
│  latency_ms INT NOT NULL          ← 检索耗时（毫秒）             │
│  embed_model_name VARCHAR(255)    ← 使用的嵌入模型名称           │
│  created_at TIMESTAMPTZ DEFAULT now()                           │
└──────────────────────────┬──────────────────────────────────────┘
                           │ 1:N
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  golden_retrieval_item                                           │
│  id UUID PK DEFAULT gen_random_uuid()                           │
│  retrieval_id UUID FK → golden_retrieval(id) ON DELETE CASCADE  │
│  chunk_id VARCHAR(512)           ← 关联的分块 ID                 │
│  score FLOAT NOT NULL            ← 相似度得分                    │
│  rank INT NOT NULL               ← 排名 (1 = 最相似)            │
└─────────────────────────────────────────────────────────────────┘
```

## API Schema

### POST /api/projects/{project_id}/golden/{record_id}/retrieval

Request:
```json
{ "max_k": 10 }
```

Response (同 GET):
```json
{
  "id": "uuid",
  "golden_id": "uuid",
  "max_k": 10,
  "latency_ms": 128,
  "embed_model_name": "bge-large-zh",
  "created_at": "2026-06-08T10:00:00Z",
  "items": [
    {
      "chunk_id": "chunk_xxx",
      "score": 0.92,
      "rank": 1,
      "content": "RAG 是检索增强生成...",
      "heading": "RAG 概述",
      "source_file": "doc1.pdf",
      "is_ground_truth": true
    }
  ]
}
```

### GET /api/projects/{project_id}/golden/{record_id}/retrieval

Response: 同上，无检索结果时返回 404

### GoldenResponse 扩展

```json
{
  "has_retrieval": true
}
```

GoldenResponse 新增 `has_retrieval` 布尔字段，前端据此决定显示「检索」还是「查看结果」按钮。

## Risks / Trade-offs

- **[检索耗时]** 单条检索可能耗时数百毫秒 → 前端显示 loading 状态
- **[覆盖丢失]** 重新检索覆盖旧结果 → 当前无历史需求，可接受；未来如需历史可改为追加模式
- **[GT 命中计算]** 后端需加载 golden record 的 ground_truth_chunks 与检索结果对比 → 数据量小（通常 < 20 条），性能无影响
- **[chunk 内容 join]** GET retrieval 需 join chunk 表 → 一次查询最多 max_k 条（默认 10），性能可控
