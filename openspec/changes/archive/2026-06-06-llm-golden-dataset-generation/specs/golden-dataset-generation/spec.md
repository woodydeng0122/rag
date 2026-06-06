## 概述

LLM 驱动的黄金数据集两阶段生成能力。用户选择文档或 chunk 后，系统串行调用 LLM 生成问题（Phase 1）和参考答案（Phase 2），以 pending_review 状态入库。

## 数据模型

### GenerateConfig（值对象）

```python
@dataclass
class GenerateConfig:
    per_chunk: int = 2                    # 每 chunk 生成问题数
    question_types: dict[str, float] = {  # 问题类型及占比
        "factual": 0.4,
        "procedural": 0.25,
        "reasoning": 0.15,
        "comparison": 0.1,
        "unanswerable": 0.1,
    }
    difficulty: str = "mixed"             # easy / medium / hard / mixed
    user_persona: str = "开发者"          # 用户群体描述
    chunk_batch_size: int = 3             # 大文件每轮 chunk 数
    file_char_threshold: int = 5000       # 文件字符数阈值
```

### GenerationTask（实体）

```python
@dataclass
class GenerationTask:
    id: str = ""
    project_id: str = ""
    status: str = "running"               # running / completed / failed
    total: int = 0                        # 预计生成总数
    completed: int = 0                    # 已完成数
    failed: int = 0                       # 失败数
    document_ids: list[str] = field(default_factory=list)
    chunk_ids: list[str] = field(default_factory=list)
    config: dict = field(default_factory=dict)
    error_message: str = ""
    created_at: datetime | None = None
    finished_at: datetime | None = None
```

## 端口

### GenerationTaskRepositoryPort

```python
class GenerationTaskRepositoryPort(ABC):
    async def save(self, task: GenerationTask) -> GenerationTask: ...
    async def get_by_id(self, task_id: str) -> GenerationTask | None: ...
    async def list_by_project(self, project_id: str) -> list[GenerationTask]: ...
    async def update(self, task: GenerationTask) -> GenerationTask: ...
```

## 用例：GenerateGoldenUseCase

### 输入

- project_id: str
- document_ids: list[str]（与 chunk_ids 二选一）
- chunk_ids: list[str]（可选，优先于 document_ids）
- config: GenerateConfig（可选，有默认值）

### 流程

1. 加载目标 chunks（按 chunk_ids 或 document_ids）
2. 创建 GenerationTask（status=running），写入 DB
3. asyncio.create_task 启动后台协程
4. 立即返回 task_id

### 后台协程执行

```
for document in selected_documents:
    chunks = load_chunks(document)
    total_chars = sum(len(c.content) for c in chunks)

    if total_chars <= config.file_char_threshold:
        # 整篇文档模式
        Phase 1: llm.generate_json(整篇文档 prompt) → 问题列表 + chunk 映射
        Phase 2: 逐问题 llm.generate_json(答案 prompt) → reference_answer
    else:
        # 分批 chunk 模式
        for batch in chunks[::config.chunk_batch_size]:
            Phase 1: llm.generate_json(chunk 批次 prompt) → 问题列表
            Phase 2: 逐问题 llm.generate_json(答案 prompt) → reference_answer

    每条结果: save GoldenRecord(status=pending_review)
    更新 task: completed += 1

异常处理:
    Phase 2 单条失败 → task.failed += 1, 跳过继续
    Phase 1 整轮失败 → task.failed += len(batch), 跳过继续

最终: 更新 task status=completed/failed
```

### Phase 1 Prompt — 整篇文档模式

输入: full_doc_text, chunks_info(id+heading列表), config
输出: `[{query, type, difficulty, answerable, ground_truth_chunks}]`

### Phase 1 Prompt — 分批 chunk 模式

输入: chunks_text(id+content), config
输出: `[{query, type, difficulty, answerable}]`（ground_truth 直接为当前 batch 的 chunk_ids）

### Phase 2 Prompt

输入: query, ground_truth_chunks_text
输出: `{reference_answer, supporting_quotes}`

### 质量评分

```python
def compute_quality_score(record) -> float:
    score = 1.0
    ans_len = len(record.reference_answer)
    if ans_len < 20 or ans_len > 300: score -= 0.2
    if len(record.ground_truth_chunks) > 3: score -= 0.1
    return round(max(score, 0.0), 2)
```

### metadata 写入

每条 GoldenRecord 的 metadata 包含:
- type: 问题类型
- difficulty: 检索难度
- answerable: 是否可回答
- quality_score: 质量评分
- supporting_quotes: 支撑引用
- source: "llm_generated"
- groundedness: "unverified"（Phase 2.5 未实现时默认值）

## API

### POST /api/projects/{pid}/golden-datasets/generate

请求体:
```json
{
  "document_ids": ["uuid1", "uuid2"],
  "chunk_ids": [],
  "config": {
    "per_chunk": 2,
    "question_types": {"factual": 0.4, "procedural": 0.25, "reasoning": 0.15, "comparison": 0.1, "unanswerable": 0.1},
    "difficulty": "mixed",
    "user_persona": "开发者"
  }
}
```

响应:
```json
{
  "task_id": "uuid",
  "status": "running"
}
```

### GET /api/projects/{pid}/generation-tasks

响应: `[{id, status, total, completed, failed, created_at, finished_at}]`

### GET /api/projects/{pid}/generation-tasks/{tid}

响应: `{id, status, total, completed, failed, document_ids, chunk_ids, config, error_message, created_at, finished_at}`

## 约束

- 串行执行，不并行多条 LLM 调用
- 文件 ≤5千字整篇处理，>5千字 3 chunk/轮
- 不做生成去重
- 不做成本/配额控制
- Phase 2 失败容忍，不回滚
