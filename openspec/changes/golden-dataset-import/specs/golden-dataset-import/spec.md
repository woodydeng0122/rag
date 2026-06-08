## ADDED Requirements

### Requirement: Golden dataset file import API
系统 SHALL 提供文件上传导入接口 `POST /api/projects/{pid}/golden/import`，支持 JSONL 和 CSV 格式。

#### Scenario: JSONL 文件导入
- **WHEN** 上传 .jsonl 文件，每行包含 query、ground_truth_chunks、reference_answer 字段
- **THEN** 解析文件内容，逐条校验并导入，返回导入结果

#### Scenario: CSV 文件导入
- **WHEN** 上传 .csv 文件，包含 query、ground_truth_chunks、reference_answer 列
- **THEN** 解析文件内容，ground_truth_chunks 列使用分号分隔，逐条校验并导入

#### Scenario: 不支持的文件格式
- **WHEN** 上传非 .jsonl 或 .csv 文件
- **THEN** 返回 400 错误，提示"仅支持 .jsonl 和 .csv 格式"

#### Scenario: 空文件
- **WHEN** 上传空文件
- **THEN** 返回 400 错误，提示"文件内容为空"

#### Scenario: 文件超过 1000 条
- **WHEN** 上传文件包含超过 1000 条记录
- **THEN** 返回 400 错误，提示"单次导入不能超过 1000 条"

### Requirement: Strict chunk ID validation on import
导入时 SHALL 严格校验 ground_truth_chunks 中的每个 chunk ID 是否存在于当前项目中，不存在的整条跳过。

#### Scenario: 所有 chunk ID 有效
- **WHEN** 某条记录的 ground_truth_chunks 中所有 ID 都存在于项目中
- **THEN** 该条记录正常导入

#### Scenario: 部分 chunk ID 无效
- **WHEN** 某条记录的 ground_truth_chunks 中有 ID 不存在于项目中
- **THEN** 该条记录跳过，导入结果中记录跳过原因为"chunk ID 不存在: xxx"

#### Scenario: ground_truth_chunks 为空
- **WHEN** 某条记录的 ground_truth_chunks 为空
- **THEN** 该条记录跳过，导入结果中记录跳过原因为"ground_truth_chunks 不能为空"

### Requirement: Import result response
导入接口 SHALL 返回详细的导入结果，包含成功数、跳过数和跳过原因列表。

#### Scenario: 部分成功
- **WHEN** 导入 10 条记录，其中 8 条成功、2 条跳过
- **THEN** 返回 `{ success_count: 8, skipped_count: 2, skipped: [{ row: 3, reason: "chunk ID 不存在: xxx" }, { row: 7, reason: "ground_truth_chunks 不能为空" }] }`

#### Scenario: 全部成功
- **WHEN** 导入 5 条记录全部成功
- **THEN** 返回 `{ success_count: 5, skipped_count: 0, skipped: [] }`

#### Scenario: 全部跳过
- **WHEN** 导入 3 条记录全部跳过
- **THEN** 返回 `{ success_count: 0, skipped_count: 3, skipped: [...] }`

### Requirement: Metadata preservation on import
导入时 SHALL 将 rag-golden-testset 生成的 metadata 信息存入 golden 表的 metadata JSONB 字段。

#### Scenario: JSONL 含 metadata
- **WHEN** 导入的 JSONL 记录包含 metadata 字段
- **THEN** metadata 完整存入 DB 的 metadata 字段

#### Scenario: CSV/JSONL 无 metadata
- **WHEN** 导入的记录不包含 metadata 字段
- **THEN** metadata 字段存入空对象 `{}`

#### Scenario: JSONL 含 quality_score 和 supporting_quotes
- **WHEN** 导入的 JSONL 记录包含 quality_score 和 supporting_quotes 字段
- **THEN** 这些字段存入 metadata 中（如 `{"quality_score": 0.9, "supporting_quotes": [...]}`）

### Requirement: Golden dataset import frontend upload button
黄金数据集页面工具栏 SHALL 新增「上传」按钮，点击弹出上传弹窗。

#### Scenario: 点击上传按钮
- **WHEN** 用户点击工具栏的「上传」按钮
- **THEN** 弹出上传弹窗，支持拖拽或点击上传文件

#### Scenario: 上传成功
- **WHEN** 文件上传成功
- **THEN** 显示导入结果（成功 N 条，跳过 M 条），刷新列表

#### Scenario: 上传失败
- **WHEN** 文件上传失败
- **THEN** 显示错误提示信息

### Requirement: Template download
上传弹窗 SHALL 提供 JSONL 和 CSV 两种模板下载链接。

#### Scenario: 下载 JSONL 模板
- **WHEN** 用户点击"JSONL 模板"链接
- **THEN** 下载包含 2 条示例记录的 .jsonl 文件

#### Scenario: 下载 CSV 模板
- **WHEN** 用户点击"CSV 模板"链接
- **THEN** 下载包含表头和 2 行示例数据的 .csv 文件

### Requirement: Import result display
导入完成后 SHALL 展示导入结果详情，包括跳过记录的原因。

#### Scenario: 有跳过记录
- **WHEN** 导入完成后有跳过的记录
- **THEN** 弹窗显示成功数和跳过数，展开可查看每条跳过记录的行号和原因

#### Scenario: 无跳过记录
- **WHEN** 导入完成后无跳过记录
- **THEN** 仅显示"成功导入 N 条记录"
