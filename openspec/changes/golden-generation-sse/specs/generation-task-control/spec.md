## ADDED Requirements

### Requirement: Pause task
系统 SHALL 提供 `POST /api/projects/{pid}/generation-tasks/{tid}/pause` 端点，暂停正在运行的生成任务。

#### Scenario: 暂停运行中的任务
- **WHEN** 用户请求暂停一个 status=running 的任务
- **THEN** 任务状态变为 paused，Runner 在当前问题处理完后停止，推送 `task_paused` 事件

#### Scenario: 暂停已暂停的任务
- **WHEN** 用户请求暂停一个 status=paused 的任务
- **THEN** 返回 400，提示任务已暂停

#### Scenario: 暂停已结束的任务
- **WHEN** 用户请求暂停一个 status=completed/failed/cancelled 的任务
- **THEN** 返回 400，提示任务已结束

### Requirement: Resume task
系统 SHALL 提供 `POST /api/projects/{pid}/generation-tasks/{tid}/resume` 端点，继续已暂停的生成任务。

#### Scenario: 继续已暂停的任务
- **WHEN** 用户请求继续一个 status=paused 的任务
- **THEN** 任务状态变为 running，Runner 继续执行，推送 `task_resumed` 事件

#### Scenario: 继续运行中的任务
- **WHEN** 用户请求继续一个 status=running 的任务
- **THEN** 返回 400，提示任务正在运行

### Requirement: Cancel task
系统 SHALL 提供 `DELETE /api/projects/{pid}/generation-tasks/{tid}` 端点，取消生成任务。已生成的黄金记录保留。

#### Scenario: 取消运行中的任务
- **WHEN** 用户请求取消一个 status=running 的任务
- **THEN** 任务状态变为 cancelled，已生成的黄金记录保留，推送 `task_cancelled` 事件

#### Scenario: 取消已暂停的任务
- **WHEN** 用户请求取消一个 status=paused 的任务
- **THEN** 任务状态变为 cancelled，已生成的黄金记录保留

#### Scenario: 取消已结束的任务
- **WHEN** 用户请求取消一个 status=completed/failed/cancelled 的任务
- **THEN** 返回 400，提示任务已结束

### Requirement: Retry failed items
系统 SHALL 提供 `POST /api/projects/{pid}/generation-tasks/{tid}/retry-failed` 端点，重新处理失败的问题。

#### Scenario: 重试失败项
- **WHEN** 用户请求重试一个有失败项的任务
- **THEN** 系统重新调用 LLM 处理失败的问题，生成结果入库，通过 SSE 推送过程

#### Scenario: 无失败项
- **WHEN** 用户请求重试一个没有失败项的任务
- **THEN** 返回 400，提示没有失败项可重试

#### Scenario: 重试时任务状态
- **WHEN** 用户请求重试
- **THEN** 任务状态必须为 completed 或 cancelled，否则返回 400

### Requirement: TaskManager manages active runners
系统 SHALL 通过 TaskManager 单例管理所有活跃的 GenerationTaskRunner 实例，提供通过 task_id 查找 Runner 的能力。

#### Scenario: 注册 Runner
- **WHEN** 新任务创建并启动 Runner
- **THEN** Runner 注册到 TaskManager

#### Scenario: 移除 Runner
- **WHEN** 任务结束（completed/failed/cancelled）
- **THEN** Runner 从 TaskManager 移除

#### Scenario: 查找不存在的 Runner
- **WHEN** 服务重启后查找之前的 Runner
- **THEN** 返回 None，API 层返回适当错误
