## Context

当前黄金数据集系统支持粗排检索（cosine/vector/bm25/hybrid），结果存储在 `golden_retrieval` + `golden_retrieval_item` 两张表中，采用覆盖模式（一个 golden_id 只保留最新一次检索）。前端 Golden.vue 表格有"检索"列展示粗排命中摘要，点击可打开检索 Drawer 查看详情。

项目已有本地嵌入模型基础设施：`EmbedderPool` + `SentenceTransformerEmbedder`，模型文件存放在 `models/` 目录。本地已有 `models/BAAI/bge-reranker-base` 模型文件。

需要新增重排能力，让用户能基于粗排结果执行 cross-encoder 重排，对比粗排与重排的 recall@k 差异。

## Goals / Non-Goals

**Goals:**
- 实现基于本地 cross-encoder（bge-reranker-base）的重排能力
- 粗排与重排结果独立存储、独立生命周期
- 前端表格新增重排列，与粗排列并列展示
- 支持批量重排（用户输入 top_k，从粗排候选中取前 N 个重排）
- 重排指标（总耗时、recall@k）与粗排指标区分展示

**Non-Goals:**
- 不实现 API 调用式 reranker（如 Cohere/Jina）
- 不实现 LLM-based reranking
- 不修改粗排的现有逻辑和数据结构
- 不实现重排模型的在线切换/配置（当前固定使用 bge-reranker-base）
- 不在检索 Drawer 中做粗排/重排对比视图（重排有独立 Drawer）

## Decisions

### D1: 数据模型 — 独立 GoldenRerank + GoldenRerankItem 表

**选择**: 新增独立表，与粗排分离存储

**备选方案**:
- A: 在 GoldenRetrievalItem 上加 rerank_score/rerank_rank 字段
- B: 独立 GoldenRerank + GoldenRerankItem 表

**理由**:
- 粗排和重排是两个独立阶段，生命周期不同（可只做粗排、可重做重排不影响粗排）
- 重排的 top_k 可能与粗排 max_k 不同（粗排 top_k=50，重排 top_k=10）
- 重排有独立指标（总耗时、模型名、recall@k）
- 符合 clean-architecture 的依赖方向，不污染已有粗排模型

**表结构**:
```
golden_rerank:
  id UUID PK
  golden_id UUID FK → golden.id (UNIQUE, 覆盖模式)
  top_k INT          ← 重排取前 N 个候选
  latency_ms INT     ← 重排总耗时
  model_name STR     ← reranker 模型名
  created_at TIMESTAMP

golden_rerank_item:
  id UUID PK
  rerank_id UUID FK → golden_rerank.id (CASCADE)
  chunk_id UUID
  original_rank INT  ← 粗排中的原始排名
  rerank_score FLOAT ← cross-encoder 分数
  rerank_rank INT    ← 重排后排名
```

### D2: Reranker 端口设计

**选择**: 新增 `RerankerPort` 端口，与 `RetrieverPort` 平级

```python
class RerankerPort(ABC):
    @abstractmethod
    async def rerank(self, query: str, documents: list[str], top_k: int) -> list[RerankResult]: ...
```

**理由**:
- 遵循 clean-architecture 依赖规则，领域层定义端口，基础设施层实现
- 与 RetrieverPort 模式一致，降低认知负担
- 未来可替换为其他 reranker 实现（API 调用等）

**适配器**: `SentenceTransformerReranker`，使用 `sentence-transformers` 的 `CrossEncoder` 类加载 `models/BAAI/bge-reranker-base`。

### D3: 重排流程

```
1. 读取粗排结果 (GoldenRetrieval + Items)
2. 取粗排前 top_k 个候选 (top_k ≤ 粗排 max_k)
3. 加载候选 chunk 的 content
4. 调用 RerankerPort.rerank(query, [chunk.content...], top_k)
5. 按 rerank_score 降序排列，分配 rerank_rank
6. 保存 GoldenRerank + GoldenRerankItem（覆盖模式）
7. 返回重排结果（含 GT 命中标记）
```

**约束**: top_k ≤ 粗排 max_k，否则报错 400。

### D4: API 设计 (RESTful)

```
POST /api/projects/{project_id}/golden/{record_id}/rerank
  Body: { top_k: int (1-100, 默认10) }
  Response: RerankResponse

GET /api/projects/{project_id}/golden/{record_id}/rerank
  Response: RerankResponse
```

与粗排 API 路径风格一致（`/retrieval` → `/rerank`）。

### D5: 前端交互

- **表格**: 新增"重排"列，位于"检索"列右侧
  - 无重排结果且无粗排结果：显示 `--`
  - 无重排结果但有粗排结果：显示蓝色「重排」按钮
  - 有重排结果：显示命中 tag（与粗排格式一致）
- **批量重排按钮**: 工具栏新增，位于"批量检索"右侧
  - 弹窗输入 top_k
  - 前置条件：选中的记录都已有粗排结果（前端校验）
- **重排 Drawer**: 与粗排 Drawer 类似，展示重排结果列表和指标
  - 指标：模型名、总耗时、top_k、recall@k（GT 命中数/GT 总数）

### D6: Reranker 实例管理

**选择**: 单例模式，在 Container 初始化时创建

**理由**:
- CrossEncoder 模型加载较慢（需读磁盘），不适合每次请求创建
- 与 EmbedderPool 模式一致（启动时加载，运行时复用）
- bge-reranker-base 模型较小（约 400MB），单例内存可接受

## Risks / Trade-offs

- **[重排耗时]** → bge-reranker-base 对每对 (query, document) 需要前向推理，top_k=50 时批量重排可能较慢。缓解：前端设置 60s 超时，后端可考虑批量推理优化。
- **[粗排结果缺失]** → 用户对未检索的记录执行重排会失败。缓解：前端校验选中记录都有粗排结果，后端返回 400 明确提示。
- **[覆盖模式]** → 重做重排会覆盖旧结果，无法对比不同 top_k 的重排效果。缓解：当前阶段可接受，后续可扩展为多版本存储。
