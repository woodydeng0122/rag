## Why

黄金数据集生成过程缓慢（每个 chunk 需 2 次 LLM 调用），但前端提交任务后完全看不到中间过程——不知道进度、看不到 LLM 交互内容、无法干预。用户只能等任务完成后刷新列表，体验差且缺乏控制力。

## What Changes

- 新增 SSE 端点，实时推送生成过程中的进度、LLM 流式输出、生成结果等事件
- 重构 `GenerateGoldenUseCase` 为事件驱动的生成器，每步 yield 事件供 SSE 推送
- 新增 `LLMPort.astream()` 异步流式生成方法，逐 token 输出
- 新增任务控制接口：暂停、继续、取消、重试失败项
- `TaskStatus` 新增 `paused`、`cancelled` 状态
- 前端交互入口从 GoldenDataset 页迁移到 DocumentList 页：
  - 文档表格"黄金数据集"列：[生成] → 参数弹窗 → 生成中(N) → 数字
  - 点击"生成中(N)"或数字 → Drawer 展示参数摘要 + 模型输出 + 入库进度
  - 工具栏新增 [批量生成] 按钮，支持多文档同时生成
  - 表格状态通过用户手动刷新更新，不轮询不推送

## Capabilities

### New Capabilities
- `generation-sse-stream`: SSE 事件流推送生成过程（进度、LLM 流式输出、生成结果）
- `generation-task-control`: 任务暂停/继续/取消/重试失败项

### Modified Capabilities
- `golden-dataset-generation`: 重构为事件驱动生成器，新增 `astream` 流式 LLM 调用，TaskStatus 新增 paused/cancelled
- `llm-json-output`: 新增 `astream` 异步流式生成方法

## Impact

- **后端 API**: 新增 5 个端点（SSE stream、pause、resume、cancel、retry-failed）
- **后端核心**: `GenerateGoldenUseCase` 重构为 `GenerationTaskRunner`，引入 `asyncio.Event` 控制暂停/取消
- **LLMPort 接口**: 新增 `astream` 抽象方法，`DashScopeLLM` 实现
- **GenerationTask 实体**: TaskStatus 枚举新增 `paused`、`cancelled`
- **前端 DocumentList.vue**: "黄金数据集"列状态流转（生成/生成中/数字），新增参数弹窗、批量生成按钮
- **前端 GenerationDrawer.vue**: 新增 Drawer 组件，展示参数摘要 + SSE 实时模型输出 + 入库进度
- **前端 GoldenDataset.vue**: 回滚 GenerationPanel 集成，恢复原始行为
- **依赖**: 无新外部依赖（FastAPI 原生支持 SSE `StreamingResponse`）
