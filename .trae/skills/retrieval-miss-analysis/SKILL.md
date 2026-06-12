---
name: "retrieval-miss-analysis"
description: "Analyzes retrieval miss reasons from golden dataset. Invoke when user wants to diagnose why retrieval missed, categorize miss types, or improve RAG recall."
---

# Retrieval Miss Analysis

分析黄金数据集中指定检索未命中条目的根因，归类到标准 miss 类型，给出改进建议。

## 触发条件

- 用户输入 `/retrieval-miss-analysis <golden_id>` 格式的命令
- golden_id 为黄金数据集中某条记录的 ID

## 执行步骤

### 1. 调用 CLI 获取指定未命中数据

```bash
source .venv/{bin|Scripts}/activate && python -m rag miss <golden_id> --format json
```

### 2. 分析 miss 原因

对该条未命中记录，根据以下信息进行分类：

**输入数据**：
- `query`: 用户查询
- `ground_truth_chunks`: 期望命中的分块（含内容、标题、源文件）
- `retrieved_chunks`: 实际检索到的分块（含内容、标题、源文件、分数、排名）
- `reference_answer`: 参考答案

### 3. Miss 分类体系

| 类型 | 英文 | 判定依据 | 典型特征 |
|------|------|----------|----------|
| **语义不匹配** | `semantic_mismatch` | 查询与 GT 分块的语义距离大，embedding 无法捕捉关联 | 查询用口语/比喻，GT 用术语；跨语言查询；同义不同词 |
| **分块边界问题** | `chunk_boundary_issue` | GT 分块在关键信息处被截断，或关键信息跨越多个分块 | GT 分块内容不完整；关键信息分散在相邻分块中 |
| **上下文污染** | `context_pollution` | 检索到的分块与查询部分相关但不是正确答案，挤占了 GT 的排名 | retrieved_chunks 中有同主题但不同子话题的分块；score 差距很小 |
| **幻觉干扰** | `hallucination` | 检索到的分块包含与查询表面匹配但实质无关的内容 | retrieved_chunks 的标题/关键词匹配但内容不相关；score 虚高 |
| **嵌入模型局限** | `embedding_limitation` | 嵌入模型本身无法区分细粒度差异 | 同一文档的多个分块语义高度相似；模型维度不足 |
| **查询歧义** | `query_ambiguity` | 查询本身模糊，多个合理解读导致 GT 不唯一 | 查询短且缺乏上下文；GT 分块与 retrieved 分块都合理 |
| **GT 标注错误** | `ground_truth_error` | GT 分块本身不是最佳答案，或标注有误 | GT 分块内容与参考答案不一致；存在更好的分块未被标注 |
| **GT 不完整** | `ground_truth_incomplete` | GT 分块内容不完整，关键信息在链接指向的其他文档中 | GT 分块只是提示横幅/导航元素；内容中包含指向其他文档的链接但答案在那边；heading 为空或缺失上下文 |
| **其他** | `other` | 不属于以上任何标准类型 | 必须在 `detail` 字段中给出自定义描述 |

### 4. 分析判定规则

对每条 miss，按以下顺序判断：

1. **检查 GT 质量**：
   - GT 分块内容与参考答案是否一致 → 不一致则归为 `ground_truth_error`
   - GT 分块是否只是提示横幅/导航元素，关键信息在链接指向的其他文档中 → 是则归为 `ground_truth_incomplete`
2. **检查分块边界**：GT 分块内容是否被截断、关键信息是否跨分块 → 是则归为 `chunk_boundary_issue`
3. **检查查询歧义**：查询是否短且模糊、是否存在多个合理解读 → 是则归为 `query_ambiguity`
4. **检查检索结果**：retrieved_chunks 是否与查询部分相关但子话题不同 → 是则归为 `context_pollution`
5. **检查语义距离**：查询与 GT 分块的语义是否需要推理/同义转换才能关联 → 是则归为 `semantic_mismatch`
6. **检查表面匹配**：retrieved_chunks 是否通过关键词/标题匹配但内容不相关 → 是则归为 `hallucination`
7. **检查嵌入模型**：GT 分块与 retrieved 分块语义高度相似但模型无法区分 → 是则归为 `embedding_limitation`
8. **兜底**：以上均不匹配 → 归为 `other`，必须在分析中详细描述具体原因

一条 miss 可以同时归为多个类型（复合原因），此时标注主因和辅因。

**判定丢失阶段**：完成 miss 类型分类后，必须判定 GT 丢失发生在哪个阶段：
1. 检查 GT chunk_id 是否出现在 retrieved_chunks 列表中
2. 不在 → 召回阶段丢失（粗排未召回 GT）
3. 在但排名超出最终截断位置 → 排序阶段丢失（粗排召回了但排名不够）

丢失阶段决定了改进建议的方向，必须与类型分类一起输出。

**重要**：`other` 不是偷懒的垃圾桶。只有经过上述 7 步逐一排除后仍无法归类的 miss 才使用 `other`，且必须给出清晰的原因描述。如果 `other` 占比超过 20%，应重新审视分类体系是否需要扩展新类型。

### 5. 输出格式

```
## 检索未命中分析报告

### <query 摘要>

- **ID**: <golden_id>
- **查询**: <完整 query>
- **主因**: <miss_type>
- **辅因**: <miss_type> (如有)
- **丢失阶段**: 召回阶段丢失 / 排序阶段丢失
- **分析**: <具体分析，说明为什么归为该类型，以及为什么判定为该丢失阶段>
- **改进建议**: <针对该 miss 类型 + 丢失阶段的改进措施，从第 7 节建议表中选择>
- **详情**: <仅当类型为 other 时必填，描述具体原因>

---

### 改进建议

<针对该 miss 类型的改进建议>
```

### 6. 判定召回阶段 vs 排序阶段

改进建议必须区分 GT 丢失发生在哪个阶段，不同阶段的改进方向完全不同：

- **召回阶段丢失**：GT 分块未出现在 retrieved_chunks 中（即粗排 top-k 内没有 GT）
  - reranker 无法解决此问题，因为 reranker 只能在已召回的结果中重排
  - 改进方向：扩大 top-k、调整 overretrieve_factor、query 改写/扩展、换用更强 embedding、调整分块策略
- **排序阶段丢失**：GT 分块在 retrieved_chunks 中但排名靠后（在 top-k 内但不在最终截断位置内）
  - 改进方向：增加 reranker 精排、调整 RRF fusion 权重、metadata 过滤、score 归一化

**判定方法**：检查 GT chunk_id 是否出现在 retrieved_chunks 列表中：
- 不在 → 召回阶段丢失
- 在但排名超出最终截断位置 → 排序阶段丢失

### 7. 各类型改进建议参考

改进建议必须结合项目现有基础设施给出，禁止建议已采用的方案。当前项目基础设施：
- **已采用**：Hybrid Search（BM25 + Cosine + RRF fusion）、overretrieve_factor=3
- **未采用**：Reranker

| 类型 | 召回阶段丢失 | 排序阶段丢失 |
|------|-------------|-------------|
| `semantic_mismatch` | query 改写/扩展；换用更强 embedding 模型；增大 top-k / overretrieve_factor | 调整 RRF fusion 权重；增加 reranker |
| `chunk_boundary_issue` | 调整分块策略（增大 chunk_size、调整 overlap）；使用语义分块；添加上下文窗口 | 同左 |
| `context_pollution` | 增大 top-k / overretrieve_factor 让 GT 进入候选；query 改写缩小范围 | 增加 reranker 精排；metadata 过滤；调整 RRF fusion 权重 |
| `hallucination` | query 改写消除歧义；增大 top-k 让 GT 进入候选 | 增加 reranker；metadata 过滤 |
| `embedding_limitation` | 升级 embedding 模型维度；使用领域微调模型；增大 top-k / overretrieve_factor | 增加 reranker 做细粒度区分 |
| `query_ambiguity` | query 扩展/改写；增加对话上下文 | 增加 reranker；metadata 过滤 |
| `ground_truth_error` | 修正 GT 标注；重新审核黄金数据集质量 | 同左 |
| `ground_truth_incomplete` | 将 GT 修正为链接指向的完整文档分块；如果目标文档未分块，该记录应从黄金数据集中清理 | 同左 |
| `other` | 根据具体原因针对性改进；如果 other 占比 >20% 建议扩展分类体系 | 同左 |

**重要**：改进建议必须从上表中选择，且必须与判定的丢失阶段匹配。禁止建议项目已采用的方案（如"添加 hybrid search"）。
