## Context

黄金数据集 CRUD 已完成（golden-dataset-crud change），支持手动逐条新增/编辑/删除/评测。DB 表 golden_dataset 已有 id、project_id、query、ground_truth_chunks、reference_answer、retrieved_chunk_ids、is_hit、hit_rank、evaluated_at、created_at 字段。

rag-golden-testset skill 生成的 JSONL 文件包含额外字段：metadata（type/difficulty/source/answerable/groundedness/expected_failure_mode）、quality_score、supporting_quotes。这些信息对评测分析有价值，不应丢弃。

现有上传模式参考：文档上传使用 multipart/form-data，上传后异步处理。黄金数据集导入是同步操作（数据量小，通常几十到几百条）。

## Goals / Non-Goals

**Goals:**
- 支持 JSONL 和 CSV 两种格式文件上传导入
- 严格校验 ground_truth_chunks 中的 chunk ID 是否存在于项目中
- 保留 rag-golden-testset 生成的完整 metadata 信息
- 提供标准模板下载（JSONL/CSV），降低数据准备门槛
- 返回详细的导入结果（成功数/跳过数/跳过原因）

**Non-Goals:**
- 不支持覆盖模式（仅追加）
- 不支持导出功能
- 不支持在线编辑 metadata
- 不做文件内容去重（query 重复时正常插入）

## Decisions

### 1. metadata 存储为 JSONB 字段

**决策**: golden_dataset 表新增 `metadata JSONB DEFAULT '{}'` 字段，存储 rag-golden-testset 生成的额外信息

**理由**: metadata 中的 type/difficulty/groundedness 等信息在评测分析时很有价值；JSONB 灵活，不预定义结构，兼容不同来源的数据；PostgreSQL JSONB 支持索引和查询

**替代方案**: 拆分为独立字段 — 字段膨胀，且无法兼容不同来源的 metadata 结构

### 2. 仅追加模式

**决策**: 导入只做追加，不提供覆盖选项

**理由**: 覆盖模式风险高（误操作可丢失数据）；用户可通过批量删除 + 导入实现覆盖效果；简化交互和后端逻辑

### 3. 严格 chunk ID 校验

**决策**: 导入时校验 ground_truth_chunks 中的每个 chunk ID 是否存在于当前项目中，不存在的整条跳过

**理由**: 无效 chunk ID 会导致评测结果不准确（recall 计算错误）；严格模式避免脏数据进入系统

**替代方案**: 宽松模式（忽略无效 ID，只保留有效的）— 可能导致用户不知道部分 chunk 已丢失

### 4. CSV 中数组用分号分隔

**决策**: CSV 格式中 ground_truth_chunks 字段使用分号分隔（如 `chunk1;chunk2`）

**理由**: 分号是 CSV 中表示列表的常见约定；逗号与 CSV 分隔符冲突；Excel 用户友好

### 5. 模板前端 Blob 生成

**决策**: 模板下载由前端 Blob 生成，不需要后端接口

**理由**: 模板内容简单固定（表头 + 2-3 行示例）；避免增加后端接口；改模板只需改前端代码

### 6. 同步导入

**决策**: 导入操作同步执行，前端等待结果

**理由**: 黄金数据集通常几十到几百条，导入耗时短（< 5s）；同步模式实现简单，用户体验直接（立即看到结果）

## Risks / Trade-offs

- **[大文件导入]** 超过 1000 条时可能耗时较长 → 限制单文件最大 1000 条，超过提示拆分
- **[CSV 编码问题]** 用户上传的 CSV 可能是 GBK 编码 → 尝试 UTF-8 解码，失败后尝试 GBK
- **[chunk ID 校验性能]** 大量记录 + 大量 chunk ID 时校验可能慢 → 一次性加载项目所有 chunk ID 到 Set 中，O(1) 查找
