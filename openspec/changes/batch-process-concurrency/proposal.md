## Why

当前批量处理文档使用 `Promise.all` 并发所有请求，存在三个问题：
1. **并发冲击**：选中 N 个文档会同时发出 N 个处理请求，embedding 模型可能被打爆（OOM/超时）
2. **无中间反馈**：处理期间按钮数字不变，用户无法感知进度，可能以为卡死
3. **一个失败全挂**：`Promise.all` 任一 reject 导致整个批量操作失败，已成功的也无法得知

## What Changes

- 批量处理改为并发 2 逐对执行，而非 Promise.all 全并发
- 每完成一对文档后，按钮数字实时递减，给用户进度反馈
- 单个文档处理失败不阻断后续，最终汇总成功/失败数量
- 处理期间禁用批量处理按钮，防止重复触发

## Capabilities

### Modified Capabilities
- `document-ui`: DocumentList.vue 批量处理交互优化 — 并发控制 + 实时反馈 + 容错

## Impact

- **前端**: DocumentList.vue 的 `handleBatchProcess` 函数重写，新增 `batchProcessing` 状态锁
