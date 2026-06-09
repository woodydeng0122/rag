## Capability: golden-retrieval

黄金记录的语义检索功能 — 支持按 query 检索 top_k chunks、持久化检索结果和指标、展示 GT 命中情况。

### 行为规范

#### 1. 触发检索

- **前置条件**: 黄金记录存在，项目已配置嵌入模型且模型在线
- **输入**: record_id, max_k (默认 10, 范围 1-100)
- **处理**:
  1. 加载黄金记录，获取 query 和 ground_truth_chunks
  2. 计时开始
  3. 调用 RetrieverPort.retrieve(query=record.query, project_id=record.project_id, top_k=max_k)
  4. 计时结束，计算 latency_ms
  5. 获取项目关联的 embed_model_name
  6. 删除该 golden_id 的旧检索结果（覆盖模式）
  7. 写入 golden_retrieval 记录（max_k, latency_ms, embed_model_name）
  8. 写入 golden_retrieval_item 列表（chunk_id, score, rank）
- **输出**: 完整检索结果（含 items、指标）
- **异常**: 记录不存在 → 404；项目无在线嵌入模型 → 400

#### 2. 获取检索结果

- **前置条件**: 黄金记录存在
- **处理**:
  1. 查询 golden_retrieval by golden_id
  2. 查询 golden_retrieval_item by retrieval_id
  3. 批量加载 chunk 内容（chunk_id → content, heading, source_file）
  4. 计算 is_ground_truth：chunk_id ∈ ground_truth_chunks → true
- **输出**: 检索结果（含 chunk 内容、GT 命中标记）
- **异常**: 无检索结果 → 404；记录不存在 → 404

#### 3. 黄金记录列表扩展

- GoldenResponse 新增 `has_retrieval` 布尔字段
- 后端查询时 LEFT JOIN golden_retrieval 判断是否存在检索结果

### 数据约束

- golden_retrieval.golden_id 是 UNIQUE 的（1:1 覆盖模式）
- golden_retrieval_item.rank 从 1 开始，按 score 降序
- 删除 golden 记录时 CASCADE 删除关联的 retrieval 和 items
- max_k 范围 1-100

### 前端交互规范

#### 表格检索列

- 无检索结果：显示蓝色「检索」按钮
- 有检索结果：显示绿色「查看结果」按钮

#### 检索 Modal

- 顶部只读显示 query 文本
- max_k 输入框，默认 10，范围 1-100
- 「确认检索」按钮，检索中显示 loading
- 检索完成后在同一 Modal 内展示结果列表

#### 检索结果展示

- 列表项按 rank 排序，显示：rank、score、GT 命中标记（●/○）、chunk 内容摘要
- 底部显示指标：embed_model_name、latency_ms、max_k、GT 命中数/ground_truth 总数
- 「重新检索」按钮（修改 max_k 后重新执行）
