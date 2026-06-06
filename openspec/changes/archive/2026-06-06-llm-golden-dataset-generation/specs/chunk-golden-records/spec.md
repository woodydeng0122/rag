## 概述

分块关联黄金记录查询。在 chunk 详情页展示该 chunk 作为 ground_truth 被引用的所有黄金记录。

## 端口扩展

### GoldenDatasetRepositoryPort

```python
async def list_by_chunk_id(
    self, chunk_id: str, project_id: str
) -> list[GoldenRecord]: ...
```

查询条件: `project_id = $1 AND $2 = ANY(ground_truth_chunks)`

## API

### GET /api/projects/{pid}/chunks/{cid}/golden-records

响应:
```json
[
  {
    "id": "uuid",
    "query": "如何配置代理？",
    "status": "pending_review",
    "reference_answer": "...",
    "metadata": {
      "type": "procedural",
      "difficulty": "easy",
      "quality_score": 0.9
    },
    "created_at": "2026-06-06T10:00:00"
  }
]
```

## 前端交互

### 分块详情弹窗新增 Tab

在现有分块详情（向量信息展示）基础上，新增"关联黄金记录"Tab:

- 列表展示: query + 状态标签 + 类型标签 + 质量评分
- 空状态: "该分块暂无关联的黄金记录"
- 点击记录可跳转到黄金数据集页面（可选）

## 约束

- 只返回当前项目的记录
- 不分页（单个 chunk 关联的记录通常不多）
- 返回所有状态的记录（pending_review / approved / rejected）
