## Chunk 按 ID 批量查询

### 概述

`ChunkRepositoryPort` 新增 `get_by_ids()` 方法，替代 `_load_chunk_map` 中的全量加载，按需查询指定 ID 的 chunk。

### 问题

当前 `GoldenRetrieveUseCase._load_chunk_map` 通过 `chunk_repo.list_by_project(limit=100000)` 加载项目下全量 chunk，再在内存中按 ID 过滤。项目 chunk 量可达 100000 条，但检索结果只需 10 条，造成严重性能浪费。

### 接口变更

#### ChunkRepositoryPort

```python
class ChunkRepositoryPort(ABC):
    # ... 现有方法 ...

    @abstractmethod
    async def get_by_ids(self, chunk_ids: list[str]) -> list[Chunk]:
        """按 ID 列表批量查询 chunk"""
        ...
```

#### PgChunkRepository 实现

```python
async def get_by_ids(self, chunk_ids: list[str]) -> list[Chunk]:
    if not chunk_ids:
        return []
    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """SELECT id, content, index, heading, source_file
               FROM chunk WHERE id = ANY($1::varchar[])""",
            chunk_ids,
        )
    return [_row_to_chunk(row) for row in rows]
```

### 调用方变更

#### GoldenRetrieveUseCase._load_chunk_map

```python
# 改前
async def _load_chunk_map(self, project_id, chunk_ids):
    all_chunks = await self._chunk_repo.list_by_project(project_id, limit=100000)
    return {c.id: c for c in all_chunks if c.id in chunk_ids}

# 改后
async def _load_chunk_map(self, project_id, chunk_ids):
    if not chunk_ids:
        return {}
    chunks = await self._chunk_repo.get_by_ids(chunk_ids)
    return {c.id: c for c in chunks}
```

### 性能预期

- 查询量从 100000 条降到 10 条（top_k=10 时）
- SQL `WHERE id = ANY($1)` 走主键索引，毫秒级返回
- 预计节省 2-5s（取决于项目 chunk 总量）
