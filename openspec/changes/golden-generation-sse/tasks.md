## 1. Domain 层变更

- [x] 1.1 TaskStatus 枚举新增 PAUSED = "paused" 和 CANCELLED = "cancelled"
- [x] 1.2 LLMPort 新增 `astream(prompt) -> AsyncGenerator[str, None]` 抽象方法

## 2. Infrastructure 层变更

- [x] 2.1 DashScopeLLM 实现 `astream` 方法，使用 AsyncOpenAI 流式输出逐 token yield

## 3. Application 层 — GenerationTaskRunner

- [x] 3.1 新建 `GenerationTaskRunner` 类，将 `_run_generation` 重构为异步生成器，每步 yield 事件字典
- [x] 3.2 Runner 持有 `pause_event: asyncio.Event`（默认 set）和 `cancel_flag: asyncio.Event`（默认 clear）
- [x] 3.3 Runner 在每条问题处理完后检查暂停/取消标志
- [x] 3.4 Runner 使用 `self.llm.astream()` 替代 `agenerate_json`，流式收集 token 并在完成时解析 JSON
- [x] 3.5 Runner 记录失败项上下文（prompt、chunk_ids）到 `failed_items` 列表
- [x] 3.6 Runner 实现 `retry_failed()` 方法，重新处理失败项并 yield 事件
- [x] 3.7 Runner 任务结束时自动 yield 终止事件（task_done / task_failed / task_cancelled）

## 4. Application 层 — TaskManager

- [x] 4.1 新建 `TaskManager` 类，管理 `dict[str, GenerationTaskRunner]`
- [x] 4.2 实现 `register(task_id, runner)`、`get(task_id)`、`remove(task_id)` 方法
- [x] 4.3 在 `bootstrap/container.py` 中注册 TaskManager 单例

## 5. API 层 — SSE 端点

- [x] 5.1 新增 `GET /api/projects/{pid}/generation-tasks/{tid}/stream` SSE 端点
- [x] 5.2 SSE 端点消费 Runner 异步生成器，格式化为 `event: xxx\ndata: {...}\n\n` 推送
- [x] 5.3 SSE 端点处理任务不存在、任务已结束等边界情况
- [x] 5.4 SSE 断线重连时推送当前 progress 事件恢复状态

## 6. API 层 — 任务控制端点

- [x] 6.1 新增 `POST /api/projects/{pid}/generation-tasks/{tid}/pause` 端点
- [x] 6.2 新增 `POST /api/projects/{pid}/generation-tasks/{tid}/resume` 端点
- [x] 6.3 新增 `DELETE /api/projects/{pid}/generation-tasks/{tid}` 取消端点
- [x] 6.4 新增 `POST /api/projects/{pid}/generation-tasks/{tid}/retry-failed` 重试端点
- [x] 6.5 各端点通过 TaskManager 查找 Runner 并执行操作，更新 DB 中任务状态

## 7. API 层 — 修改现有 generate 端点

- [x] 7.1 修改 `POST /golden-datasets/generate`，使用 GenerationTaskRunner + TaskManager 替代原有 UseCase

## 8. 前端 — 生成面板组件

- [x] 8.1 新建 `GenerationPanel.vue` 组件，可折叠面板展示生成过程
- [x] 8.2 面板顶部展示进度条（completed/total/failed）和控制按钮（暂停/继续/取消）
- [x] 8.3 面板主体按文档分组展示 Phase 1 问题列表和 Phase 2 答案流式输出
- [x] 8.4 失败项旁显示 [重试] 按钮
- [x] 8.5 使用 `EventSource` 消费 SSE 事件流，解析事件类型渲染 UI

## 9. 前端 — 集成到 GoldenDataset.vue

- [x] 9.1 在 GoldenDataset.vue 中引入 GenerationPanel 组件
- [x] 9.2 修改 `handleGenerate` 方法，提交任务后打开面板并建立 SSE 连接
- [x] 9.3 生成过程中用户可继续操作表格（面板不阻塞表格交互）
- [x] 9.4 SSE 断线重连逻辑：重新建立 EventSource，从 progress 事件恢复面板状态
