---
name: rag-retrieval-eval
description: 用黄金测试集评测 RAG 检索器质量，计算 recall@k、MRR、Hit Rate 等指标。当用户提到「recall@k」、「检索评测」、「retrieval eval」、「测试检索质量」、「MRR」、「Hit Rate」、「评测 retriever」时触发。输入 golden_testset.jsonl + 检索器，输出指标报告，并给出是否回溯分块策略的结论。是整个 RAG 黄金测试集流程的最终验证环节。
---

# RAG 检索评测

## 职责边界

**只做一件事**：用黄金测试集量化检索器的召回质量，给出达标结论。

---

## 输入

| 参数 | 必填 | 说明 |
|------|------|------|
| golden_testset.jsonl | ✅ | rag-golden-testset 的输出 |
| retriever | ✅ | 实现 `.search(query, top_k) -> List[{id, score}]` 接口 |
| k 值列表 | 否 | 默认 `[1, 3, 5, 10]` |

## 输出

- 控制台指标报告
- `retrieval_eval_report.json`

---

## 三个核心指标

### Recall@k

> 黄金 chunk 是否出现在 top-k 召回结果中

```python
def recall_at_k(retriever, records, k):
    hits = 0
    answerable = [r for r in records if r["ground_truth_chunks"]]
    for r in answerable:
        retrieved = {c["id"] for c in retriever.search(r["query"], top_k=k)}
        if set(r["ground_truth_chunks"]) & retrieved:
            hits += 1
    return hits / len(answerable) if answerable else 0.0
```

### MRR（Mean Reciprocal Rank）

> 黄金 chunk 首次出现的排名倒数均值，衡量排序质量

```python
def mrr(retriever, records, k=10):
    scores = []
    for r in records:
        if not r["ground_truth_chunks"]:
            continue
        retrieved = [c["id"] for c in retriever.search(r["query"], top_k=k)]
        gt = set(r["ground_truth_chunks"])
        rr = next((1/(i+1) for i, cid in enumerate(retrieved) if cid in gt), 0)
        scores.append(rr)
    return sum(scores) / len(scores) if scores else 0.0
```

### Hit Rate@k

> 至少命中一个黄金 chunk 的问题占比（与 Recall@k 相同，此处语义对齐 RAGAS 框架）

```python
def hit_rate_at_k(retriever, records, k):
    return recall_at_k(retriever, records, k)   # 语义等价
```

---

## 按问题类型分析

不同类型的问题 recall 差异，能定位检索器的具体短板：

```python
def eval_by_type(retriever, records, k=5):
    from collections import defaultdict
    buckets = defaultdict(list)
    for r in records:
        buckets[r["metadata"]["type"]].append(r)
    return {
        qtype: recall_at_k(retriever, items, k)
        for qtype, items in buckets.items()
    }
```

---

## 完整评测主函数

```python
def run_eval(retriever, golden_path: str, k_list=[1,3,5,10]):
    import json
    records = [json.loads(l) for l in open(golden_path)]

    results = {
        "recall": {k: recall_at_k(retriever, records, k) for k in k_list},
        "mrr":    mrr(retriever, records),
        "by_type": eval_by_type(retriever, records, k=5),
        "total":  len(records),
        "answerable": len([r for r in records if r["ground_truth_chunks"]]),
    }
    return results
```

---

## 输出评测报告

```
RAG 检索评测报告
══════════════════════════════════════
测试集：        golden_testset.jsonl
总题数：        200（含 20 道无答案题）

核心指标：
  recall@1  =  0.54
  recall@3  =  0.71
  recall@5  =  0.76   ⚠️
  recall@10 =  0.83
  MRR       =  0.61

按问题类型（recall@5）：
  factual      0.88  ✅
  procedural   0.79  ✅
  reasoning    0.61  ⚠️
  comparison   0.48  ❌  ← 跨 chunk 问题召回差

结论：【⚠️ 有优化空间】
══════════════════════════════════════
```

---

## 结果解读与行动建议

| recall@5 | 结论 | 建议行动 |
|----------|------|----------|
| ≥ 0.80 | ✅ 检索质量良好 | 接入生成器，进行端到端评测 |
| 0.65 ~ 0.79 | ⚠️ 有优化空间 | 尝试混合检索（BM25 + 向量）或 Reranker |
| < 0.65 | ❌ 检索质量差 | **回溯 rag-chunk-splitter**，调整分块策略 |

### 按类型定向优化

| 短板类型 | 根因 | 调整方向 |
|----------|------|----------|
| `comparison` 低 | 相关内容分散在多个 chunk | 加大 overlap，或用 HyDE 查询扩展 |
| `reasoning` 低 | chunk 边界截断了推理链 | 改用 semantic 分块 |
| `factual` 低 | chunk 粒度太粗 | 缩小 chunk_size |
| 全类型普遍低 | embedding 模型与领域不匹配 | 换领域微调的 embedding 模型 |

---

## 回溯信号

以下情况应回溯到 `rag-chunk-splitter` 重新切分，而不是调优检索器：

- recall@5 < 0.65
- `comparison` 类 recall@5 < 0.50（跨 chunk 信息被切断）
- MRR < 0.50（黄金 chunk 排名靠后，说明相关性信号弱）
