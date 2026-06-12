## MODIFIED Requirements

### Requirement: Trigger project evaluation with top_k
系统 SHALL 提供项目评估统计 API，重排评估需校验项目是否配置了重排模型。

#### Scenario: 正常粗排评估
- **WHEN** 请求 `POST /api/projects/{pid}/evaluation-stats`，body 为 `{ top_k: 10, category: "recall" }`
- **THEN** 后端从 golden_retrieval + golden_retrieval_item 表加载该项目的检索结果，按 rank <= top_k 过滤，计算指标并持久化

#### Scenario: 正常重排评估
- **WHEN** 请求 `POST /api/projects/{pid}/evaluation-stats`，body 为 `{ top_k: 10, category: "rerank" }`，且项目已配置重排模型
- **THEN** 后端从 golden_rerank + golden_rerank_item 表加载该项目的重排结果，按 rerank_rank <= top_k 过滤，计算指标并持久化

#### Scenario: 重排评估但项目未配置重排模型
- **WHEN** 请求 `POST /api/projects/{pid}/evaluation-stats`，body 为 `{ category: "rerank" }`，但项目 `rerank_model_id` 为 NULL
- **THEN** 返回 400 错误，提示"项目未配置重排模型"

#### Scenario: 项目无重排结果
- **WHEN** 请求 `POST /api/projects/{pid}/evaluation-stats`，body 为 `{ category: "rerank" }`，项目已配置重排模型但无重排结果
- **THEN** 返回 400 错误，提示"项目无重排结果，请先执行重排"
