## 1. 前端状态

- [x] 1.1 新增 `batchProcessing` ref，控制批量处理按钮禁用状态

## 2. 批量处理逻辑重写

- [x] 2.1 重写 `handleBatchProcess`：过滤 ready 文档 → 确认弹窗 → 并发 2 逐对执行
- [x] 2.2 实现并发控制：每次取 2 个 id 并行处理，完成后从 selectedRowKeys 移除，再取下一对
- [x] 2.3 逐个 try/catch：失败记录到 failedIds，不阻断后续
- [x] 2.4 处理完成后汇总：成功 N 个，失败 M 个（如有失败则 message.warning，否则 message.success）

## 3. 按钮状态

- [x] 3.1 批量处理按钮增加 `:disabled="selectedRowKeys.length === 0 || batchProcessing"` 条件
- [x] 3.2 处理期间按钮显示 loading 状态
