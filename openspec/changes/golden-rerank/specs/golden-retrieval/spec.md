## MODIFIED Requirements

### Requirement: 黄金记录列表扩展

系统 SHALL 在黄金记录列表响应中同时包含粗排和重排摘要信息。

原规范仅包含 `has_retrieval` 和 `retrieval_summary`，现扩展新增 `has_rerank` 和 `rerank_summary`。

- GoldenResponse 新增 `has_rerank` 布尔字段
- GoldenResponse 新增 `rerank_summary` 字段（结构：hit_count, gt_total, hit_ranks）
- 后端查询时批量获取重排命中摘要（与粗排摘要并行查询）

#### Scenario: 列表同时包含粗排和重排摘要
- **WHEN** 获取黄金记录列表，某条记录同时有粗排和重排结果
- **THEN** 该记录的 has_retrieval=true, retrieval_summary 有值, has_rerank=true, rerank_summary 有值

#### Scenario: 列表中有粗排无重排
- **WHEN** 获取黄金记录列表，某条记录有粗排但无重排
- **THEN** 该记录的 has_retrieval=true, has_rerank=false, rerank_summary=null

#### Scenario: 列表中无粗排无重排
- **WHEN** 获取黄金记录列表，某条记录无粗排也无重排
- **THEN** 该记录的 has_retrieval=false, has_rerank=false, retrieval_summary=null, rerank_summary=null
