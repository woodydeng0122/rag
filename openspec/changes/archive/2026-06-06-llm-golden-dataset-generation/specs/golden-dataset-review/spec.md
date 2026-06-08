## 概述

黄金数据集审批流程。LLM 生成的记录以 pending_review 状态入库，用户可逐条或批量 approve/reject。rejected 记录保留展示，提供删除操作。

## 数据模型变更

### GoldenRecord.status

新增字段，取值:
- `pending_review`: 待审核（LLM 生成入库的默认状态）
- `approved`: 已审批（手动创建的默认状态）
- `rejected`: 已拒绝

### GoldenDatasetRepositoryPort 扩展

```python
class GoldenDatasetRepositoryPort(ABC):
    # 已有方法: save, get_by_id, list_by_project, update, delete

    async def list_by_project_and_status(
        self, project_id: str, status: str
    ) -> list[GoldenRecord]: ...

    async def update_status(
        self, record_id: str, status: str
    ) -> GoldenRecord: ...

    async def batch_update_status(
        self, record_ids: list[str], status: str
    ) -> int: ...
```

## 用例扩展：GoldenDatasetUseCase

### approve(record_id) -> GoldenRecord

将单条记录 status 从 pending_review 改为 approved。

### reject(record_id) -> GoldenRecord

将单条记录 status 从 pending_review 改为 rejected。

### batch_approve(record_ids) -> int

批量将记录 status 改为 approved，返回更新条数。

### batch_reject(record_ids) -> int

批量将记录 status 改为 rejected，返回更新条数。

## API

### PATCH /api/projects/{pid}/golden/{rid}

请求体（扩展 UpdateGoldenDatasetRequest）:
```json
{
  "status": "approved",
  "query": "可选，同时修改",
  "ground_truth_chunks": ["可选"],
  "reference_answer": "可选"
}
```

### POST /api/projects/{pid}/golden/batch-approve

请求体:
```json
{
  "record_ids": ["uuid1", "uuid2", "uuid3"]
}
```

响应:
```json
{
  "updated_count": 3
}
```

### POST /api/projects/{pid}/golden/batch-reject

请求体:
```json
{
  "record_ids": ["uuid1", "uuid2"]
}
```

响应:
```json
{
  "updated_count": 2
}
```

### GET /api/projects/{pid}/golden 扩展

新增查询参数 `status`:
- `?status=pending_review` — 只返回待审核记录
- `?status=approved` — 只返回已审批记录
- `?status=rejected` — 只返回已拒绝记录
- 无参数 — 返回全部

## 前端交互

### GoldenDataset.vue 工具栏新增

- 状态筛选下拉: 全部 / 待审核 / 已审批 / 已拒绝
- 批量审批按钮: 选中记录后可批量 approve
- 批量拒绝按钮: 选中记录后可批量 reject

### 表格新增列

- 状态列: 🟡待审核 / 🟢已通过 / 🔴已拒绝
- 操作列: 审批/拒绝按钮（仅 pending_review 状态显示）

### rejected 记录

- 保留在列表中，灰色/半透明样式
- 提供删除操作
- 可重新编辑后 approve

## 约束

- approved 记录可参与评测（EvaluateUseCase 只查 approved 记录）
- rejected 记录不参与评测
- 手动创建的记录默认 approved
- status 变更不影响评测结果（已评测的记录改 status 后评测数据保留）
