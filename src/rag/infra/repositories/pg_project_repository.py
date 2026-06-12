from rag.domain.entities.project import Project
from rag.domain.ports.project_repository import ProjectRepositoryPort
from rag.infra.repositories.base import BaseRepository, to_uuid


class PgProjectRepository(ProjectRepositoryPort, BaseRepository):
    """PostgreSQL 实现的项目仓储"""

    _SELECT = """SELECT id, name, description, embed_model_id, embed_dimension,
                        rerank_model_id, user_id, created_at, updated_at
                 FROM project"""

    async def save(self, project: Project) -> Project:
        row = await self._fetch_one(
            """INSERT INTO project (name, description, embed_model_id, embed_dimension, rerank_model_id, user_id)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id, name, description, embed_model_id, embed_dimension,
                      rerank_model_id, user_id, created_at, updated_at""",
            project.name,
            project.description,
            to_uuid(project.embed_model_id) if project.embed_model_id else None,
            project.embed_dimension,
            to_uuid(project.rerank_model_id) if project.rerank_model_id else None,
            to_uuid(project.user_id) if project.user_id else None,
        )
        return _row_to_project(row)

    async def get_by_id(self, project_id: str) -> Project | None:
        row = await self._fetch_one(
            f"{self._SELECT} WHERE id = $1",
            to_uuid(project_id),
        )
        if row is None:
            return None
        return _row_to_project(row)

    async def get_by_name(self, name: str) -> Project | None:
        row = await self._fetch_one(
            f"{self._SELECT} WHERE name = $1",
            name,
        )
        if row is None:
            return None
        return _row_to_project(row)

    async def list(self, user_id: str | None = None) -> list[Project]:
        if user_id:
            rows = await self._fetch_all(
                f"{self._SELECT} WHERE user_id = $1 ORDER BY created_at DESC",
                to_uuid(user_id),
            )
        else:
            rows = await self._fetch_all(
                f"{self._SELECT} ORDER BY created_at DESC"
            )
        return [_row_to_project(row) for row in rows]

    async def update(self, project: Project) -> Project:
        row = await self._fetch_one(
            """UPDATE project SET name = $1, description = $2, updated_at = now()
            WHERE id = $3
            RETURNING id, name, description, embed_model_id, embed_dimension,
                      rerank_model_id, user_id, created_at, updated_at""",
            project.name,
            project.description,
            to_uuid(project.id),
        )
        if row is None:
            raise ValueError(f"项目 {project.id} 不存在")
        return _row_to_project(row)

    async def delete(self, project_id: str) -> bool:
        return await self._delete_by_id("project", project_id)


def _row_to_project(row) -> Project:
    embed_model_id = row["embed_model_id"]
    rerank_model_id = row["rerank_model_id"]
    user_id = row["user_id"]
    return Project(
        id=str(row["id"]),
        name=row["name"],
        description=row["description"] or "",
        embed_model_id=str(embed_model_id) if embed_model_id else "",
        embed_dimension=row["embed_dimension"] or 512,
        rerank_model_id=str(rerank_model_id) if rerank_model_id else "",
        user_id=str(user_id) if user_id else "",
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )
