---
name: rag-golden-testset
description: 用两阶段方式生成 RAG 黄金测试集：先从源文档提炼自然问题，再映射回 chunk 确定 ground_truth。当用户提到「黄金测试集」、「golden test set」、「生成测试集」、「问答对生成」、「构建 eval 数据集」、「RAG benchmark」时触发。输入源文档 + chunks.jsonl（需已通过 rag-chunk-quality-check），输出标准化 JSONL/CSV，含 query、ground_truth_chunks、reference_answer 三元组，可直接用于 RAGAS、TruLens、LlamaIndex Evaluator 等评测框架。
---

# RAG 黄金测试集生成

## 职责边界

**只做一件事**：用两阶段方式把源文档转化为高质量问答三元组。

**为什么需要两阶段？**
- 只从 chunk 生问题：问题质量受 chunk 边界限制，容易碎片化，不贴近真实用户
- 只从源文档生问题：无法精确定位 ground_truth_chunks，recall@k 无法计算
- **两阶段**：从源文档保证问题自然，映射回 chunk 保证评测可计算

**前提条件**：
- `chunks.jsonl` 必须已通过 `rag-chunk-quality-check` 达标
- 源文档（原始文本）需与 chunks 来自同一份材料
- 如果用户只提供 chunks 未提供源文档，先用 chunk 文本拼接还原，并提示质量可能略低

---

## 输入

| 参数 | 必填 | 说明 |
|------|------|------|
| 源文档 | ✅ | 原始文档文本，用于生成自然问题 |
| chunks.jsonl | ✅ | rag-chunk-quality-check 达标后的 chunk 文件，用于映射 ground_truth |
| 测试规模 | 否 | 小型 50 / 中型 200 / 大型 500+，默认 100 |
| 用户群体描述 | 否 | 影响问题风格，如「开发者」「非技术用户」 |
| 目标评测框架 | 否 | RAGAS / LlamaIndex / 自定义，影响输出格式 |
| 问题类型偏好 | 否 | 如「多流程型，少事实型」 |

## 输出

- `golden_testset.jsonl`

---

## 问题类型矩阵

| 类型 | 说明 | 默认占比 | 来源 |
|------|------|----------|------|
| `factual` | 直接从文本提取答案 | 40% | 单 chunk |
| `procedural` | 询问步骤/方法 | 25% | 单 chunk |
| `reasoning` | 需要推断或理解因果 | 15% | 单 chunk |
| `comparison` | 对比两个概念 | 10% | 跨 chunk |
| `unanswerable` | 语料中无答案（测试拒答） | 10% | 无 chunk |

---

## 生成流程

```
源文档（完整语义）
    ↓
  Phase 1：从源文档生成问题   ← 保证问题自然，不受 chunk 边界干扰
    ↓
  Phase 1.5：质量过滤 + 语义去重 ← 过滤空泛问题，去除语义重复
    ↓
  Phase 2：问题映射回 chunk   ← BM25→Embedding→Rerank→LLM Judge，确定 ground_truth_chunks
    ↓
  丢弃无法映射的问题
    ↓
  Phase 3：生成标准答案       ← 基于命中的 chunk 文本生成
    ↓
  Phase 3.5：答案 groundedness 校验 ← 确保答案有据可查，不通过则重新生成
    ↓
  Phase 4：组装三元组 → golden_testset.jsonl
```

---

### Phase 1：从源文档生成问题

读完整文档，不受 chunk 边界限制，生成贴近真实用户的问题。

**Prompt — 可回答问题**：

```
你是 RAG 评测数据生成专家。仔细阅读以下完整文档，
生成 {n} 个真实用户可能提出的问题。

规则：
- 不要考虑文档如何被切分，只关注文档传达的知识点
- 风格贴近真实用户提问（{user_persona}）
- 覆盖不同类型：事实、流程、推理、对比
- 不要直接复制原文句子作为问题
- difficulty 按"检索难度"标注，不是"答案难度"：
  - easy：query 关键词与原文高度重叠，检索器容易命中
  - medium：query 需要跨 2 个 chunk，或用词与原文有差异
  - hard：query 需要推理/跨段综合，或用词与原文差异大，检索器容易漏
- 只输出 JSON 数组，不要有其他内容

文档：
{full_doc_text}

输出格式：
[
  {"query": "...", "type": "factual|procedural|reasoning|comparison", "difficulty": "easy|medium|hard"},
  ...
]
```

**Prompt — 无答案问题（Hard Negative，占 10%，测试拒答能力）**：

```
根据以下文档的主题范围，生成 {n} 个看起来与文档相关、但文档实际上无法回答的问题。

要求：
- 问题看起来专业、合理，容易误导检索器召回相关 chunk
- 但仔细阅读后，文档中确实没有答案
- 不要生成明显无关或荒谬的问题
- 优先生成"看似相关但细节超出文档范围"的问题

文档主题摘要：{topic_summary}

文档关键词：{doc_keywords}

输出格式（JSON 数组）：
[{"query": "...", "type": "unanswerable", "difficulty": "hard"}]
```

> **为什么需要 Hard Negative？** 真实场景中，检索器最常犯的错误是召回"看起来相关但实际无关"的 chunk。Hard Negative 专门测试这种 retrieval miss + hallucination 风险。

---

### Phase 1.5：质量过滤 + 语义去重

Phase 1 生成的问题可能包含空泛、重复或无评测价值的问题，需要过滤和去重。

**Step A — Query Quality Filter**：

```
判断以下问题是否适合作为 RAG 评测问题。

标准：
- 是否具体（不是泛泛而谈）
- 是否可被文档回答（不是常识问题）
- 是否有评测区分度（不是所有系统都能答对或都答错）
- 是否不是纯定义类问题（如"什么是X？"）

问题：{query}

输出 JSON：
{"keep": true/false, "reason": "..."}
```

> **典型应过滤的问题**："什么是 FastAPI？"、"如何使用 API？"、"介绍一下 OAuth"——这些太泛，无法区分检索器质量。

**Step B — Semantic Dedup**：

```python
def semantic_dedup(queries: list[str], embed_fn, threshold: float = 0.88) -> list[str]:
    """基于 embedding 余弦相似度去重，保留先出现的那个"""
    if not queries:
        return queries
    embeddings = [embed_fn(q) for q in queries]
    keep = [True] * len(queries)
    for i in range(len(queries)):
        if not keep[i]:
            continue
        for j in range(i + 1, len(queries)):
            if not keep[j]:
                continue
            sim = cosine_similarity(embeddings[i], embeddings[j])
            if sim > threshold:
                keep[j] = False
    return [q for q, k in zip(queries, keep) if k]
```

> **阈值参考**：0.88 是经验值。低于 0.85 可能误删不同问题，高于 0.92 可能漏掉语义重复。

---

### Phase 2：问题映射回 Chunk

对每个问题，找出哪些 chunk 包含回答所需的信息。
找不到 ground_truth 的问题直接丢弃（说明问题质量有问题或文档覆盖不足）。

**Prompt — chunk 映射**：

```
给定一个问题和若干文本片段，判断哪些片段包含回答该问题所需的信息。

问题：{query}

文本片段：
{chunks_json}   // [{"id": "...", "text": "..."}]

规则：
- 只选真正包含答案依据的片段
- 如果没有任何片段能回答该问题，返回空数组
- 只输出 JSON，不要解释

输出格式：
{"ground_truth_chunks": ["chunk_id_1", "chunk_id_2"]}
```

**映射实现（两阶段检索）**：

```python
import json

def retrieve_candidates(query: str, chunks: list[dict], embed_fn, top_k: int = 50) -> list[dict]:
    """BM25 → Embedding → Rerank 三级候选筛选"""
    # Stage 1: BM25 粗筛 top-100
    bm25_hits = bm25_search(query, chunks, top_k=100)
    # Stage 2: Embedding 精排 top-50
    query_emb = embed_fn(query)
    scored = [(c, cosine_similarity(query_emb, embed_fn(c["text"]))) for c in bm25_hits]
    scored.sort(key=lambda x: x[1], reverse=True)
    # Stage 3: Rerank（可选，如有 reranker）
    top50 = [c for c, _ in scored[:top_k]]
    if reranker_available():
        top50 = rerank(query, top50, top_k=20)
    return top50

def map_to_chunks(query: str, chunks: list[dict], embed_fn, llm_call) -> list[str]:
    """BM25→Embedding→Rerank→LLM Judge，返回 ground_truth chunk id 列表"""
    candidates = retrieve_candidates(query, chunks, embed_fn, top_k=50)
    payload = [{"id": c["id"], "text": c["text"][:300]} for c in candidates[:20]]

    response = llm_call(query=query, chunks_json=json.dumps(payload, ensure_ascii=False))
    result = json.loads(response)
    gt = result.get("ground_truth_chunks", [])
    # 限制最多 5 个 chunk，避免过度映射
    return gt[:5]

def filter_unmappable(questions: list[dict], chunks: list[dict], embed_fn, llm_call) -> list[dict]:
    """丢弃无法映射到任何 chunk 的问题"""
    mapped = []
    for q in questions:
        if q["type"] == "unanswerable":
            mapped.append({**q, "ground_truth_chunks": []})
            continue
        gt_chunks = map_to_chunks(q["query"], chunks, embed_fn, llm_call)
        if gt_chunks:                          # 能映射才保留
            mapped.append({**q, "ground_truth_chunks": gt_chunks})
    return mapped
```

> **为什么需要两阶段检索？** 纯 BM25 只能做关键词匹配，会漏掉语义相关但用词不同的 chunk。加 Embedding 精排 + Rerank 后，映射准确率显著提升，直接影响 recall@k 评测的可信度。
>
> **Multi-label 规则**：`ground_truth_chunks` 最多 5 个。真实 RAG 中答案常跨多个 chunk，但超过 5 个说明问题太泛或映射过于宽松。
>
> **丢弃率参考**：正常情况下 10-20% 的问题会因映射失败被丢弃。丢弃率 > 30% 说明问题质量或 chunk 质量有问题，建议检查。

**静态 Failure Mode 标注**：

映射完成后，基于 query 和 ground_truth_chunks 的特征，推断潜在检索失败风险。这是静态规则标注，不需要运行 retriever。

```python
def infer_failure_mode(query: str, gt_chunks: list[dict]) -> list[str]:
    """基于 query-GT 特征推断潜在检索失败模式"""
    modes = []
    if not gt_chunks:
        return modes
    # 规则 1：GT chunk 文本与 query 关键词重叠度低 → retrieval_miss
    query_tokens = set(jieba.cut(query))
    chunk_tokens = set()
    for c in gt_chunks:
        chunk_tokens |= set(jieba.cut(c["text"]))
    overlap_ratio = len(query_tokens & chunk_tokens) / max(len(query_tokens), 1)
    if overlap_ratio < 0.3:
        modes.append("retrieval_miss")
    # 规则 2：答案跨多个 chunk → chunk_boundary
    if len(gt_chunks) > 1:
        modes.append("chunk_boundary")
    # 规则 3：query 类型为 reasoning/comparison → semantic_mismatch
    # （这类问题用词通常与原文差异大）
    return modes
```

> **为什么是静态标注？** 真实的 failure mode 依赖于具体 retriever 的表现，属于 `rag-retrieval-eval` 的职责。这里的静态标注提供"潜在风险"信号，帮助在数据生成阶段就识别高风险问题，无需运行 retriever。

---

### Phase 3：生成标准答案

基于映射到的 chunk 文本生成答案，保证答案有据可查。

```
根据以下文本片段，回答问题。

规则：
- 答案完全基于给定文本，不引入外部知识
- 简洁准确，20-300 字
- 如果文本中没有答案，回答"该问题在文档中无对应信息"

文本片段：
{ground_truth_chunks_text}

问题：{query}

输出格式（JSON）：
{"reference_answer": "...", "supporting_quotes": ["原文片段1", "原文片段2"]}
```

---

### Phase 3.5：答案 Groundedness 校验

Phase 3 生成的答案可能引入外部知识（hallucinate），需要校验答案是否完全基于 ground_truth_chunks。

**Prompt — Groundedness Check**：

```
判断以下答案是否完全基于给定的文本片段。

文本片段：
{ground_truth_chunks_text}

答案：{reference_answer}

判断标准：
- supported：答案中的每个论点都能在文本中找到依据
- partially_supported：答案部分内容有依据，部分无依据
- unsupported：答案主要依赖外部知识，文本中无法支撑

输出 JSON：
{"groundedness": "supported|partially_supported|unsupported", "unsupported_claims": ["..."]}
```

**校验逻辑**：

```python
def validate_groundedness(record: dict, llm_call, max_retries: int = 1) -> dict:
    """校验答案 groundedness，不通过则重新生成（最多重试 max_retries 次）"""
    for _ in range(max_retries + 1):
        result = llm_call(
            ground_truth_chunks_text=record["chunks_text"],
            reference_answer=record["reference_answer"]
        )
        check = json.loads(result)
        if check["groundedness"] == "supported":
            record["metadata"]["groundedness"] = "supported"
            return record
    # 重试后仍不通过，标记但保留（供人工审核）
    record["metadata"]["groundedness"] = check["groundedness"]
    record["metadata"]["unsupported_claims"] = check.get("unsupported_claims", [])
    return record
```

> **为什么需要 Groundedness Check？** 没有这个校验，Phase 3 生成的 reference_answer 可能包含幻觉，导致 eval 时把"正确幻觉"当成 ground_truth，污染评测结果。

---

### Phase 4：组装三元组

```python
def compute_quality_score(q: dict, answer_obj: dict) -> float:
    """基于多维度计算单条记录质量分（0-1）"""
    score = 1.0
    # 惩罚：答案过短或过长
    ans_len = len(answer_obj.get("reference_answer", ""))
    if ans_len < 20 or ans_len > 300:
        score -= 0.2
    # 惩罚：ground_truth_chunks 过多（说明问题太泛）
    if len(q.get("ground_truth_chunks", [])) > 3:
        score -= 0.1
    # 惩罚：groundedness 不通过
    if q.get("metadata", {}).get("groundedness") != "supported":
        score -= 0.3
    return round(max(score, 0.0), 2)

def build_record(q: dict, answer_obj: dict, qid: int) -> dict:
    metadata = {
        "type":       q["type"],
        "difficulty": q.get("difficulty", "medium"),
        "source":     q.get("source", "N/A"),
        "answerable": q["type"] != "unanswerable",
        "groundedness": q.get("metadata", {}).get("groundedness", "unverified"),
        "expected_failure_mode": q.get("expected_failure_mode", []),
    }
    record = {
        "id":                  f"q_{qid:04d}",
        "query":               q["query"],
        "ground_truth_chunks": q["ground_truth_chunks"],
        "reference_answer":    answer_obj["reference_answer"],
        "supporting_quotes":   answer_obj.get("supporting_quotes", []),
        "metadata":            metadata,
        "quality_score":       compute_quality_score({**q, "metadata": metadata}, answer_obj),
    }
    return record
```

---

## 输出格式

### JSONL（主格式，兼容 RAGAS / LlamaIndex）

```jsonl
{"id":"q_0001","query":"向量数据库和传统数据库的区别？","ground_truth_chunks":["intro_chunk_0003"],"reference_answer":"向量数据库...","supporting_quotes":["..."],"metadata":{"type":"comparison","difficulty":"easy","source":"intro.md","answerable":true,"groundedness":"supported","expected_failure_mode":[]},"quality_score":0.9}
```

### CSV（人工审核）

```csv
id,query,ground_truth_chunks,reference_answer,type,difficulty,source,answerable,groundedness,expected_failure_mode,quality_score
q_0001,向量数据库和传统数据库的区别？,intro_chunk_0003,向量数据库...,comparison,easy,intro.md,true,supported,[],0.9
```

### RAGAS 专用转换

```python
from datasets import Dataset

def to_ragas(records, chunks_map):
    return Dataset.from_dict({
        "question":    [r["query"] for r in records],
        "ground_truth":[r["reference_answer"] for r in records],
        "contexts":    [[chunks_map[cid] for cid in r["ground_truth_chunks"]]
                        for r in records],
    })
```

---

## 测试集自检清单

生成完成后自动执行：

```
□ query 未直接复制原文专有名词
□ reference_answer 长度 20-300 字
□ ground_truth_chunks 非空（unanswerable 除外）
□ ground_truth_chunks 数量 ≤ 5（超过说明问题太泛）
□ 类型分布：factual ≤ 50%
□ 难度分布：easy ≈ 30% / medium ≈ 50% / hard ≈ 20%
□ unanswerable 占比 8-15%
□ 问题去重：语义相似度 < 0.88
□ quality_filter 通过率 ≥ 70%（低于说明 Phase 1 问题质量差）
□ groundedness = supported 占比 ≥ 80%（低于说明答案幻觉严重）
□ quality_score 均值 ≥ 0.7（低于说明整体质量需人工审核）
```

---

## 完成后

输出摘要后，提示用户可以调用 `rag-retrieval-eval` 跑 recall@k 验证测试集与检索器的闭环质量。
