from abc import ABC, abstractmethod

from rag.domain.entities.project_evaluation import ProjectEvaluation


class ProjectEvaluationRepositoryPort(ABC):
    """项目评估统计仓储端口"""

    @abstractmethod
    async def save(self, evaluation: ProjectEvaluation) -> ProjectEvaluation:
        """保存评估结果"""
        ...

    @abstractmethod
    async def list_by_project(self, project_id: str) -> list[ProjectEvaluation]:
        """按项目查询评估历史，按 created_at 降序"""
        ...
