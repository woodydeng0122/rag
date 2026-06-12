from abc import ABC, abstractmethod

from rag.domain.entities.project_evaluation import ProjectEvaluation
from rag.domain.value_objects.retrieval_strategy import RetrievalStrategy


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

    @abstractmethod
    async def delete(self, evaluation_id: str) -> bool:
        """删除评估记录，返回是否成功"""
        ...

    @abstractmethod
    async def update(self, evaluation_id: str, **kwargs) -> bool:
        """更新评估记录字段，返回是否成功"""
        ...
