## 1. 数据库 Migration

- [x] 1.1 创建 migration: golden 表新增 metadata JSONB DEFAULT '{}' 字段

## 2. Domain 层

- [x] 2.1 更新 GoldenRecord 实体：新增 metadata: dict 字段，默认空字典

## 3. Infra 层

- [x] 3.1 更新 PgGoldenDatasetRepository：save/update 读写 metadata 字段，_row_to_record 解析 metadata

## 4. Application 层

- [x] 4.1 GoldenDatasetUseCase 新增 import_records 方法：解析 JSONL/CSV、严格 chunk ID 校验、追加导入、返回 ImportResult
- [x] 4.2 新增 ImportResult 数据类：success_count、skipped_count、skipped 列表

## 5. API 层

- [x] 5.1 新增 ImportGoldenDatasetResponse schema：success_count、skipped_count、skipped 列表
- [x] 5.2 新增 POST /api/projects/{pid}/golden/import 路由：接收 multipart 文件上传
- [x] 5.3 更新 GoldenDatasetResponse schema：新增 metadata 字段
- [x] 5.4 更新 golden 路由的 _record_to_response：输出 metadata
- [x] 5.5 路由改为 RESTful 风格：/golden (复数) + /golden/{id} + /golden/import

## 6. 前端 API 层

- [x] 6.1 新增 api/model/goldenDatasetModel.ts：ImportResult 类型、SkippedRecord 类型
- [x] 6.2 新增 api/goldenDataset.ts：importGoldenDataset API 调用（multipart 上传）

## 7. 前端页面

- [x] 7.1 GoldenDataset.vue 工具栏新增「上传」按钮（UploadOutlined 图标）
- [x] 7.2 实现上传弹窗：拖拽/点击上传、格式说明（支持 .jsonl / .csv）
- [x] 7.3 实现模板下载：JSONL 模板（Blob 生成，2 条示例）、CSV 模板（Blob 生成，表头 + 2 行示例）
- [x] 7.4 实现导入结果展示：成功数/跳过数 + 跳过原因列表
- [x] 7.5 更新 GoldenDatasetItem 类型：新增 metadata 字段
