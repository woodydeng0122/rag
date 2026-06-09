## 检索异步任务

### 概述

将检索操作从同步阻塞改为异步任务模式：API 立即返回 task_id，后台执行检索，前端轮询获取结果。

### 数据模型

#### RetrievalTask（内存对象）

```python
@dataclass
class RetrievalTask:
    id: str                          # UUID
    golden_id: str                   # 关联的黄金记录 ID
    status: str                      # pending / running / completed / failed
    result: GoldenRetrievalResult | None  # 完成后的检索结果
    error: str | None                # 失败时的错误信息
    created_at: datetime             # 创建时间
```

#### RetrievalTaskManager（模块级单例）

```python
class RetrievalTaskManager:
    _tasks: dict[str, RetrievalTask]
    _semaphore: asyncio.Semaphore(2)  # 控制并发度

    async def create_task(self, golden_id: str, max_k: int) -> RetrievalTask
    async def create_batch_tasks(self, golden_ids: list[str], max_k: int) -> list[RetrievalTask]
    def get_task(self, task_id: str) -> RetrievalTask | None
    def _run_task(self, task: RetrievalTask, max_k: int) -> None  # 后台协程
```

### API 接口

#### POST /api/projects/{pid}/golden/{id}/retrieval

触发异步检索，立即返回任务信息。

请求体：
```json
{ "max_k": 10 }
```

响应（200）：
```json
{
  "code": 0,
  "message": "ok",
  "result": {
    "task_id": "uuid",
    "golden_id": "uuid",
    "status": "pending"
  }
}
```

#### GET /api/projects/{pid}/golden/retrieval/tasks/{task_id}

查询任务状态和结果。

响应 — 进行中（200）：
```json
{
  "code": 0,
  "message": "ok",
  "result": {
    "task_id": "uuid",
    "golden_id": "uuid",
    "status": "running",
    "result": null,
    "error": null
  }
}
```

响应 — 已完成（200）：
```json
{
  "code": 0,
  "message": "ok",
  "result": {
    "task_id": "uuid",
    "golden_id": "uuid",
    "status": "completed",
    "result": {
      "id": "uuid",
      "golden_id": "uuid",
      "max_k": 10,
      "latency_ms": 20000,
      "embed_latency_ms": 15000,
      "search_latency_ms": 3000,
      "embed_model_name": "bge-large-zh",
      "created_at": "...",
      "items": [...]
    },
    "error": null
  }
}
```

响应 — 失败（200）：
```json
{
  "code": 0,
  "message": "ok",
  "result": {
    "task_id": "uuid",
    "golden_id": "uuid",
    "status": "failed",
    "result": null,
    "error": "项目未配置在线嵌入模型"
  }
}
```

#### POST /api/projects/{pid}/golden/batch-retrieval

批量触发检索，为每条记录创建独立任务。

请求体：
```json
{
  "record_ids": ["uuid1", "uuid2", "uuid3"],
  "max_k": 10
}
```

响应（200）：
```json
{
  "code": 0,
  "message": "ok",
  "result": {
    "tasks": [
      { "task_id": "uuid", "golden_id": "uuid1", "status": "pending" },
      { "task_id": "uuid", "golden_id": "uuid2", "status": "pending" },
      { "task_id": "uuid", "golden_id": "uuid3", "status": "pending" }
    ]
  }
}
```

#### GET /api/projects/{pid}/golden/{id}/retrieval（保持不变）

刷新页面时获取已持久化的检索结果。

### 前端交互

#### 单条检索

1. 点击"检索" → `POST /retrieval` → 拿到 `task_id`
2. 每 2s 轮询 `GET /tasks/{task_id}`
3. `status === "completed"` → 展示结果，停止轮询
4. `status === "failed"` → 展示错误，停止轮询
5. 超过 5 分钟 → 提示超时，停止轮询

#### 批量检索

1. 点击"批量检索" → `POST /batch-retrieval` → 拿到任务列表
2. 并行轮询所有任务（每 2s 一次批量查询）
3. 进度展示："3/10 已完成"
4. 全部完成 → 刷新列表，停止轮询

#### 超时策略

- 检索相关请求（`POST /retrieval`, `GET /tasks/{id}`）timeout 设为 30s
- 其他请求保持 15s 不变
