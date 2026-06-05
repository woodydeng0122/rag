## Requirements

### Requirement: Evaluate by project and golden IDs
评测 API SHALL 改为 `POST /api/projects/{pid}/evaluate`，body 包含 golden_ids 和可选的 k_list，后端从 DB 加载黄金数据执行评测。

#### Scenario: 批量评测
- **WHEN** 请求 `POST /api/projects/{pid}/evaluate`，body 为 `{ golden_ids: ["id1", "id2"], k_list: [10] }`
- **THEN** 后端从 DB 加载对应黄金记录，逐条检索并计算指标，返回评测结果

#### Scenario: 单条评测
- **WHEN** 请求 `POST /api/projects/{pid}/evaluate`，body 为 `{ golden_ids: ["id1"] }`
- **THEN** 后端对该单条记录执行评测并返回结果

#### Scenario: golden_ids 为空
- **WHEN** 请求 `POST /api/projects/{pid}/evaluate`，golden_ids 为空列表
- **THEN** 返回 400 错误，提示"golden_ids 不能为空"

### Requirement: Persist evaluation results to golden records
评测完成后 SHALL 将每条记录的评测结果持久化到 golden_dataset 表的 retrieved_chunk_ids、is_hit、hit_rank、evaluated_at 字段。

#### Scenario: 命中记录持久化
- **WHEN** 某条记录的 ground_truth_chunks 与 retrieved_chunk_ids 有交集
- **THEN** is_hit 设为 True，hit_rank 设为首个命中分块的排名位置，evaluated_at 设为当前时间

#### Scenario: 未命中记录持久化
- **WHEN** 某条记录的 ground_truth_chunks 与 retrieved_chunk_ids 无交集
- **THEN** is_hit 设为 False，hit_rank 设为 None，evaluated_at 设为当前时间

### Requirement: Persist evaluation summary to project
评测完成后 SHALL 将汇总指标持久化到 project 表的 eval_recall_at_10、eval_mrr、eval_answerable、eval_total、eval_latency_avg_ms、evaluated_at 字段。

#### Scenario: 评测汇总更新
- **WHEN** 批量评测完成
- **THEN** project 表的评测字段更新为本次评测的汇总值，evaluated_at 设为当前时间

#### Scenario: 部分成功时汇总
- **WHEN** 批量评测中部分记录成功部分失败
- **THEN** 已成功记录的评测结果持久化，project 汇总基于成功记录计算，响应中标记失败记录

### Requirement: EvaluateUseCase refactor
EvaluateUseCase SHALL 重构为支持从 DB 加载黄金数据并持久化评测结果，新增 GoldenDatasetRepositoryPort 依赖。

#### Scenario: 从 DB 加载黄金数据
- **WHEN** 调用 execute(project_id, golden_ids, k_list)
- **THEN** 通过 GoldenDatasetRepositoryPort 从 DB 加载对应记录

#### Scenario: 评测结果回写
- **WHEN** 评测计算完成
- **THEN** 通过 GoldenDatasetRepositoryPort 更新每条记录的评测字段，通过 ProjectRepositoryPort 更新项目汇总
