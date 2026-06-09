## Why

黄金数据集页面当前只有 CRUD 和审批流程，缺少检索验证能力。用户无法在页面上直接对某条黄金记录执行语义检索、查看检索结果与 ground_truth 的匹配情况。需要为每条黄金记录增加检索功能，支持按 query 执行语义检索、记录检索指标（耗时、模型、max_k）、展示检索结果并标记 GT 命中。

## What Changes

- 新增 `golden_retrieval` 和 `golden_retrieval_item` 两张数据库表，独立存储检索结果（方案 B）
- 新增 Domain 层实体：`GoldenRetrieval`、`GoldenRetrievalItem`，端口：`GoldenRetrievalRepositoryPort`
- 新增 Application 层用例：`GoldenRetrieveUseCase`，组合检索 + 持久化 + GT 命中计算
- 新增 API 端点：`POST /golden/{id}/retrieval`（触发检索，覆盖旧结果）、`GET /golden/{id}/retrieval`（获取检索结果，后端 join chunk 内容 + GT 命中标记）
- 前端 Golden.vue 表格新增「检索」列：无结果时显示检索按钮，有结果时显示查看结果按钮
- 前端新增检索 Modal：输入 max_k（默认 10），展示检索结果列表（含 GT 命中标记、chunk 内容、score、rank）

## Capabilities

### New Capabilities
- `golden-retrieval`: 黄金记录的语义检索功能，支持按 query 检索 top_k chunks、持久化检索结果和指标、展示 GT 命中情况

### Modified Capabilities
- `golden-dataset-crud`: 黄金数据集表格新增检索列，GoldenRecord 列表响应新增 has_retrieval 标记

## Impact

- **数据库**: 新增 2 张表（golden_retrieval、golden_retrieval_item），1 个 migration
- **后端 Domain**: 新增 2 个实体、1 个端口
- **后端 Infra**: 新增 1 个 PG 仓储实现
- **后端 Application**: 新增 1 个用例，Container 新增注册
- **后端 API**: golden 路由新增 2 个端点，schemas 新增请求/响应类型
- **前端**: Golden.vue 加检索列 + Modal，API 层新增 2 个方法，Model 层新增类型
