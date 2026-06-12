## Context

当前系统中，粗排嵌入模型已通过 `embed_model` 注册表 + `project.embed_model_id` FK 实现了项目级配置。但重排模型（reranker）是全局硬编码的：

- `SentenceTransformerReranker` 在 `container.py` 中以固定 `model_path="models/BAAI/bge-reranker-base"` 实例化
- `GoldenRerankUseCase` 中 `model_name` 硬编码为 `"BAAI/bge-reranker-base"`
- 所有项目共享同一个重排模型实例，无法按项目区分

本地 `models/` 目录下同时存在嵌入模型和重排模型，但 `ModelScanner` 只扫描嵌入模型（依赖 `modules.json` + `hidden_size`），重排模型被忽略。

## Goals / Non-Goals

**Goals:**
- `embed_model` 注册表同时管理嵌入模型和重排模型，通过 `model_type` 列区分
- 项目可独立配置重排模型（`project.rerank_model_id` FK），也可不配置（NULL = 不走重排）
- `ModelScanner` 一次扫描同时发现嵌入模型和重排模型
- `RerankerPool` 支持按 `model_path` 缓存多个 `CrossEncoder` 实例
- `rerank_model_id = NULL` 时，重排和重排评估拒绝触发，问答/检索不受影响

**Non-Goals:**
- 问答/检索流程加重排环节（未来可扩展，本次不做）
- 远程 API 重排模型（如 DashScope reranker）的支持
- 重排模型的动态上下线管理（复用现有 `embed_model.status` 机制即可）

## Decisions

### D1: 复用 `embed_model` 表 + `model_type` 列，而非独立 `rerank_model` 表

**选择**: 在 `embed_model` 表加 `model_type VARCHAR(32) NOT NULL DEFAULT 'embed'` 列

**理由**:
- 嵌入模型和重排模型共享大部分字段（id, name, description, status, metadata, created_at, updated_at）
- 统一注册表简化扫描、管理、前端选择器
- `dimension` 对 reranker 无意义，设为 0，`EmbedModel.ensure_complete()` 按 `model_type` 跳过校验

**备选**: 独立 `rerank_model` 表 — 语义更纯但多一张表、多一套 CRUD、前端两个选择器，复杂度翻倍

### D2: `model_type` 判定依据 — `modules.json` 是否存在

**选择**: 扫描时检查 `model_dir/modules.json` 是否存在

```python
is_embed = (model_dir / "modules.json").exists()
model_type = "embed" if is_embed else "reranker"
```

**理由**:
- SentenceTransformer 嵌入模型必定有 `modules.json`（定义 Transformer → Pooling → Normalize 流水线）
- CrossEncoder 重排模型没有 `modules.json`
- 这是 SentenceTransformer 生态的标准区分方式，可靠且无歧义

**备选**: 检查 `architectures` 字段中是否包含 `*ForSequenceClassification` — 不够通用，有些嵌入模型也可能有此 architecture

### D3: `rerank_model_id` 可选（NULL = 不走重排）

**选择**: `project.rerank_model_id UUID REFERENCES embed_model(id) DEFAULT NULL`

**理由**:
- 向后兼容 — 已有项目无需迁移即可正常工作
- 语义清晰 — NULL = 该项目不使用重排
- 问答/检索流程不涉及重排，不受影响
- 重排/重排评估触发时前置校验 `rerank_model_id` 是否为空

### D4: RerankerPool 设计 — 与 EmbedderPool 对称

**选择**: 新增 `RerankerPool`，按 `model_path` 缓存 `CrossEncoder` 实例

```
RerankerPool
├── factory: type[CrossEncoder]
├── _pool: dict[str, CrossEncoder]   # model_path → instance
├── max_size: int
└── get(model_path: str) → CrossEncoder
```

**理由**:
- 多项目可能使用不同重排模型，需要多实例缓存
- 与 `EmbedderPool` 设计对称，降低认知负担
- `CrossEncoder` 加载慢（几秒），缓存避免重复加载

### D5: reranker 的 `dimension` 处理

**选择**: reranker 类型 `dimension=0`，`EmbedModel.ensure_complete()` 按 `model_type` 跳过校验

**理由**:
- reranker 不产出向量，`dimension` 无意义
- `dimension=0` 比 `NULL` 更简单，不需要改列约束
- 校验逻辑调整为：`model_type == "embed"` 时才校验 `dimension > 0`

## Risks / Trade-offs

- **[Risk] `embed_model` 表语义变宽** → `model_type` 列明确区分，查询时始终带 `WHERE model_type = ?` 过滤，避免混淆
- **[Risk] 已有 `embed_model` 行缺少 `model_type`** → 迁移脚本 `UPDATE embed_model SET model_type = 'embed' WHERE model_type IS NULL`，一次性补全
- **[Risk] `RerankerPool` 内存占用** → `max_size` 限制缓存数量，LRU 淘汰；当前本地只有 1 个 reranker 模型，实际压力小
- **[Trade-off] `dimension=0` 对 reranker 不优雅** → 但避免了改列为 NULLABLE 的连锁影响，代价可接受
