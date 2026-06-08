## Why

当前黄金数据集仅支持手动逐条新增，无法批量导入。rag-golden-testset skill 生成的 JSONL/CSV 测试集无法直接导入系统，用户需要逐条手动录入，效率极低。需要支持文件上传批量导入，并提供标准模板下载，降低数据准备门槛。

## What Changes

- 新增黄金数据集文件上传 API，支持 JSONL 和 CSV 两种格式
- golden 表新增 metadata JSONB 字段，保留 rag-golden-testset 生成的完整信息（type、difficulty、quality_score 等）
- 后端实现文件解析、严格 chunk ID 校验、追加导入逻辑，返回导入结果（成功数/跳过数/跳过原因）
- 前端新增上传按钮和上传弹窗（拖拽上传 + 格式说明）
- 前端提供 JSONL/CSV 模板下载（Blob 生成）
- 导入结果展示：成功 N 条，跳过 M 条 + 原因列表

## Capabilities

### New Capabilities
- `golden-import`: 黄金数据集文件上传导入，支持 JSONL/CSV 格式，严格 chunk ID 校验，追加模式

### Modified Capabilities
- `golden-crud`: GoldenRecord 实体和 DB 表新增 metadata JSONB 字段，API 响应包含 metadata

## Impact

- **后端 Domain**: GoldenRecord 实体新增 metadata 字段
- **后端 Infra**: PgGoldenDatasetRepository 读写 metadata，新增 DB migration
- **后端 Application**: GoldenDatasetUseCase 新增 import_records 方法
- **后端 API**: 新增 /import 端点，schemas 新增导入请求/响应
- **前端**: GoldenDataset.vue 新增上传按钮、上传弹窗、模板下载
- **前端 API**: goldenDataset.ts 新增导入 API 调用
