## ADDED Requirements

### Requirement: DocumentList golden column state flow
DocumentList 文档表格"黄金数据集"列 SHALL 展示三态流转：[生成] → 生成中(N) → 数字。

#### Scenario: 无记录且文档 ready
- **WHEN** 文档 status=ready 且 golden_record_count=0
- **THEN** 显示 [生成] 按钮

#### Scenario: 生成中
- **WHEN** 用户提交生成任务后
- **THEN** 该行"黄金数据集"列显示"生成中(N)"蓝色链接，N 为已完成数
- **AND** 前端本地维护 doc_id → task_id 映射

#### Scenario: 生成完成
- **WHEN** 用户刷新页面后文档有黄金记录
- **THEN** 显示数字（如"5"）绿色链接

#### Scenario: 表格状态更新方式
- **WHEN** 生成任务提交后
- **THEN** 不自动刷新表格，用户手动刷新获取最新状态

### Requirement: Generation parameter modal
点击 [生成] 或 [批量生成] 时 SHALL 弹出参数选择弹窗。

#### Scenario: 参数弹窗内容
- **WHEN** 弹窗打开
- **THEN** 展示：每分块问题数（默认2）、用户画像（默认"开发者"）、问题类型（多选）

#### Scenario: 提交生成
- **WHEN** 用户点击 [开始生成]
- **THEN** 调用 POST /golden/generate，提交后关闭弹窗，更新该行状态为"生成中(0)"

### Requirement: Batch generation
工具栏 SHALL 新增 [批量生成] 按钮，支持多文档同时生成。

#### Scenario: 批量生成
- **WHEN** 用户勾选多个文档并点击 [批量生成]
- **THEN** 弹出参数弹窗，提交后每个文档独立创建生成任务
- **AND** 各行"黄金数据集"列独立显示"生成中"

#### Scenario: 未勾选文档
- **WHEN** 用户点击 [批量生成] 但未勾选任何文档
- **THEN** 按钮禁用

### Requirement: GenerationDrawer component
点击"生成中(N)"或已完成数字时 SHALL 打开 Drawer 展示生成详情。

#### Scenario: 点击"生成中"打开 Drawer
- **WHEN** 用户点击"生成中(N)"
- **THEN** 打开 Drawer，建立 SSE 连接实时展示生成过程
- **AND** Drawer 展示：参数摘要、进度条、控制按钮（暂停/继续/取消）、模型输出区域

#### Scenario: 点击数字打开 Drawer
- **WHEN** 用户点击已完成的数字
- **THEN** 打开 Drawer，展示已生成的记录列表（只读模式）

#### Scenario: Drawer 参数摘要区域
- **WHEN** Drawer 打开
- **THEN** 展示关键参数摘要（每分块题数、用户画像、问题类型），不展示完整 prompt

#### Scenario: Drawer 模型输出区域
- **WHEN** SSE 推送事件
- **THEN** 实时展示 Phase 1 问题列表和 Phase 2 答案流式输出
- **AND** 失败项旁显示 [重试] 按钮

#### Scenario: SSE 连接管理
- **WHEN** 同时只打开一个 Drawer 的 SSE 连接
- **THEN** 切换 Drawer 时断开旧连接，建立新连接
