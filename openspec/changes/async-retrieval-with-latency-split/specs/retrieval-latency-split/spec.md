## 检索耗时拆分

### 概述

将检索总耗时 `latency_ms` 拆分为 `embed_latency_ms`（嵌入 API 调用耗时）和 `search_latency_ms`（向量检索耗时），便于定位性能瓶颈。

### 数据库变更

#### 迁移脚本 009_split_retrieval_latency.sql

```sql
ALTER TABLE golden_retrieval ADD COLUMN embed_latency_ms INT NOT NULL DEFAULT 0;
ALTER TABLE golden_retrieval ADD COLUMN search_latency_ms INT NOT NULL DEFAULT 0;
```

### 领域实体变更

#### GoldenRetrieval

```python
@dataclass
class GoldenRetrieval:
    golden_id: str
    max_k: int
    latency_ms: int
    embed_latency_ms: int = 0       # 新增
    search_latency_ms: int = 0      # 新增
    embed_model_name: str
    id: str = ""
    created_at: datetime | None = None
```

### RetrieverPort 返回类型变更

#### 新增 RetrievalOutput

```python
@dataclass
class RetrievalOutput:
    results: list[RetrievalResult]
    embed_latency_ms: int    # 嵌入 API 调用耗时
    search_latency_ms: int   # 向量检索耗时
```

#### RetrieverPort 接口变更

```python
class RetrieverPort(ABC):
    @abstractmethod
    async def retrieve(self, query: str, project_id: str, top_k: int = 3) -> RetrievalOutput: ...
```

### CosineRetriever 计时实现

```python
async def retrieve(self, query, project_id, top_k=3) -> RetrievalOutput:
    # ... 加载嵌入矩阵、获取模型 ...

    # 计时: 嵌入
    embed_start = time.monotonic()
    query_vectors = embedder.embed(query)
    embed_latency_ms = int((time.monotonic() - embed_start) * 1000)

    # 计时: 向量检索
    search_start = time.monotonic()
    scores = np.dot(embeddings_array, query_emb)
    sorted_indices = scores.argsort()
    best_indices = sorted_indices[-top_k:][::-1]
    search_latency_ms = int((time.monotonic() - search_start) * 1000)

    results = [RetrievalResult(chunk_id=embeddings[i].chunk_id, score=float(scores[i])) for i in best_indices]

    return RetrievalOutput(
        results=results,
        embed_latency_ms=embed_latency_ms,
        search_latency_ms=search_latency_ms,
    )
```

### API Schema 变更

#### RetrievalResponse

```python
class RetrievalResponse(BaseModel):
    id: str
    golden_id: str
    max_k: int
    latency_ms: int
    embed_latency_ms: int = 0       # 新增
    search_latency_ms: int = 0      # 新增
    embed_model_name: str = ""
    created_at: str = ""
    items: list[RetrievalItemResponse] = Field(default_factory=list)
```

### 前端展示

检索结果指标区域新增两个 Tag：

```
[模型: bge-large-zh] [总耗时: 20000ms] [嵌入: 15000ms] [检索: 3000ms] [max_k: 10] [命中GT: 3/5]
```
