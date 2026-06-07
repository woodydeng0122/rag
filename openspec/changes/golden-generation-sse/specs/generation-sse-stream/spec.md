## ADDED Requirements

### Requirement: SSE event stream endpoint
系统 SHALL 提供 `GET /api/projects/{pid}/generation-tasks/{tid}/stream` 端点，返回 `text/event-stream` 响应，实时推送生成过程事件。

#### Scenario: 成功建立 SSE 连接
- **WHEN** 客户端请求 `GET /generation-tasks/{tid}/stream` 且任务存在且状态为 running
- **THEN** 返回 `Content-Type: text/event-stream`，开始推送事件

#### Scenario: 任务不存在
- **WHEN** 客户端请求的 task_id 不存在
- **THEN** 返回 404

#### Scenario: 任务已结束
- **WHEN** 客户端请求已 completed/failed/cancelled 任务的 stream
- **THEN** 推送最终状态事件后关闭连接

### Requirement: Progress event
系统 SHALL 在每条问题处理完成后推送 `progress` 事件，包含 `completed`、`total`、`failed` 字段。

#### Scenario: 进度更新
- **WHEN** 一条问题处理完成（成功或失败）
- **THEN** 推送 `event: progress\ndata: {"completed": N, "total": M, "failed": F}`

### Requirement: Phase start event
系统 SHALL 在每个处理阶段开始时推送 `phase_start` 事件，标识当前阶段（question_gen 或 answer_gen）。

#### Scenario: 问题生成阶段开始
- **WHEN** 开始调用 LLM 生成问题
- **THEN** 推送 `event: phase_start\ndata: {"phase": "question_gen", "doc_id": "xxx"}`

#### Scenario: 答案生成阶段开始
- **WHEN** 开始为某条问题生成答案
- **THEN** 推送 `event: phase_start\ndata: {"phase": "answer_gen", "query_index": N}`

### Requirement: LLM token stream event
系统 SHALL 在 LLM 流式输出时逐 token 推送 `llm_token` 事件。

#### Scenario: 流式 token 推送
- **WHEN** LLM 返回一个 token
- **THEN** 推送 `event: llm_token\ndata: {"content": "token文本"}`

#### Scenario: LLM 输出完成
- **WHEN** LLM 流式输出结束
- **THEN** 推送 `event: llm_done\ndata: {"raw_length": N}`

### Requirement: Question generated event
系统 SHALL 在 Phase 1 解析出每条问题时推送 `question_generated` 事件。

#### Scenario: 问题生成成功
- **WHEN** Phase 1 LLM 返回的问题列表解析成功
- **THEN** 对每条问题推送 `event: question_generated\ndata: {"index": N, "query": "...", "type": "factual", "difficulty": "medium"}`

### Requirement: Result event
系统 SHALL 在每条问题的完整处理（Phase 1 + Phase 2）结束后推送 `result` 事件。

#### Scenario: 问题处理成功
- **WHEN** 一条问题的问题生成和答案生成均成功
- **THEN** 推送 `event: result\ndata: {"query": "...", "answer": "...", "chunk_ids": [...], "quality_score": 0.8, "status": "success"}`

#### Scenario: 问题处理失败
- **WHEN** 一条问题的处理过程中发生错误
- **THEN** 推送 `event: result\ndata: {"query": "...", "status": "failed", "error": "错误信息"}`

### Requirement: Task terminal events
系统 SHALL 在任务结束时推送终止事件并关闭 SSE 连接。

#### Scenario: 任务完成
- **WHEN** 所有文档处理完毕
- **THEN** 推送 `event: task_done\ndata: {"completed": N, "failed": M}` 并关闭连接

#### Scenario: 任务异常
- **WHEN** 任务执行过程中发生未捕获异常
- **THEN** 推送 `event: task_failed\ndata: {"error": "错误信息"}` 并关闭连接

#### Scenario: 任务取消
- **WHEN** 任务被用户取消
- **THEN** 推送 `event: task_cancelled\ndata: {}` 并关闭连接

### Requirement: SSE reconnection
系统 SHALL 支持 SSE 断线重连，重连后从 DB 读取最新进度恢复面板状态。

#### Scenario: 断线重连
- **WHEN** 客户端 SSE 连接断开后重新连接
- **THEN** 推送当前 `progress` 事件恢复进度，继续推送后续事件

#### Scenario: 不补发历史事件
- **WHEN** 客户端重连
- **THEN** 不补发断线期间的 `llm_token` 和 `result` 事件
