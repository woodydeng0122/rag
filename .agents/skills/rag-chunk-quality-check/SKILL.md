---
name: rag-chunk-quality-check
description: 检查 RAG chunks 的质量并输出报告。当用户提到「检查 chunk」、「chunk 质量」、「分块质量」、「chunk quality」、「验证分块」时触发。输入 chunks.jsonl，从结构完整性、长度分布、语义自洽性、重复冗余四个维度检查，输出质量报告和达标/不达标结论，不达标时给出调整建议。是 rag-chunk-splitter 的下游、rag-golden-testset 的上游门控。
---

# Chunk 质量检查

## 职责边界

**只做一件事**：判断 chunks 是否达到生成黄金测试集的质量门槛。

---

## 输入

| 参数 | 必填 | 说明 |
|------|------|------|
| chunks.jsonl | ✅ | rag-chunk-splitter 的输出，或用户自有 chunk 文件 |

## 输出

- 控制台质量报告（含结论）
- `chunk_quality_report.json`（可选，供后续脚本消费）

---

## 四个检查维度

### 维度一：结构完整性

```python
import re

def check_truncation(text: str) -> bool:
    """末尾是否有完整标点"""
    return bool(re.search(r'[。！？.!?…」』]$', text.rstrip()))

def check_noise(text: str) -> bool:
    """是否为噪声 chunk"""
    patterns = [
        r'^\s*第\s*\d+\s*页\s*$',
        r'^\s*(目录|索引|参考文献|附录)\s*$',
        r'^\s*[=\-_]{5,}\s*$',
        r'^\s*$',
    ]
    return any(re.match(p, text) for p in patterns)

def check_header_orphan(text: str) -> bool:
    """只有标题没有正文"""
    lines = text.strip().splitlines()
    return len(lines) == 1 and lines[0].startswith('#')
```

### 维度二：长度分布

```python
import numpy as np

def length_stats(chunks: list[dict]) -> dict:
    lengths = [c["char_count"] for c in chunks]
    return {
        "total":     len(chunks),
        "min":       min(lengths),
        "max":       max(lengths),
        "mean":      round(np.mean(lengths)),
        "p5":        round(np.percentile(lengths, 5)),
        "p95":       round(np.percentile(lengths, 95)),
        "too_short": sum(1 for l in lengths if l < 100),
        "too_long":  sum(1 for l in lengths if l > 1500),
    }
```

### 维度三：语义自洽性

规则检测（全量）：

```python
DANGLING = ['它', '他们', '她们', '该方法', '上述', '前者', '后者', '此处', '如上所述']

def check_dangling(text: str) -> list[str]:
    """检测悬空代词——chunk 开头或前 30 字出现无指代对象的代词"""
    return [p for p in DANGLING
            if text.startswith(p) or f'，{p}' in text[:30] or f'。{p}' in text[:30]]
```

LLM 打分（抽样 10%）：

```
判断以下文本片段是否语义完整、能独立表达一个意思。
1 = 明显截断，读不懂
3 = 能读懂但强依赖上下文
5 = 完全自洽，独立成段

文本：{chunk_text}
只输出数字，不要解释。
```

### 维度四：重复与冗余

```python
from difflib import SequenceMatcher

def find_duplicates(chunks: list[dict], threshold: float = 0.8) -> list[tuple]:
    pairs = []
    for i in range(len(chunks)):
        for j in range(i + 1, len(chunks)):
            r = SequenceMatcher(None, chunks[i]["text"], chunks[j]["text"]).ratio()
            if r > threshold:
                pairs.append((chunks[i]["id"], chunks[j]["id"], round(r, 2)))
    return pairs
```

---

## 达标阈值

| 指标 | 阈值 | 不达标时的调整建议 |
|------|------|-------------------|
| 噪声 chunk | = 0 条 | 清洗后重新切 |
| 过短（< 100字符） | ≤ 2% | 提高 min_chunk_size 或合并相邻 chunk |
| 过长（> 1500字符） | ≤ 5% | 调小 chunk_size |
| 句子截断率 | ≤ 15% | overlap 从 50 → 100 |
| 悬空代词率 | ≤ 10% | 改用 semantic 分块策略 |
| LLM 自洽抽样 | ≥ 8/10 | 调整分块策略后重新抽样 |
| 高相似度对（> 0.8） | ≤ 1% | 去重后再送入下游 |

---

## 输出质量报告

```
Chunk 质量报告
══════════════════════════════════════
总 chunk 数：          342
平均长度：             487 字符
长度范围：             p5=120 / p95=980

检查结果：
  ❌ 噪声 chunk：        7 条  ( 2.0%)  → 必须清洗
  ❌ 过短 chunk：       18 条  ( 5.3%)  → 合并或过滤
  ⚠️  句子截断：         41 条  (12.0%)  → overlap 50 → 100
  ⚠️  悬空代词：         23 条  ( 6.7%)  → 考虑 semantic 策略
  ⚠️  高相似度对：       12 对           → 去重
  ✅  LLM 自洽抽样：   8/10 通过

结论：【不达标】
建议：清洗 7 条噪声 → 调整 overlap=100 重新切分 → 再次检查
══════════════════════════════════════
```

达标时输出：

```
结论：【✅ 达标】可以进入 rag-golden-testset 生成测试集
```

---

## 完成后

- 不达标：列出具体调整参数，提示回到 `rag-chunk-splitter` 重新切
- 达标：提示用户可以调用 `rag-golden-testset`，并将 `chunks.jsonl` 路径传入
