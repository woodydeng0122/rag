import logging

from rag.application.usecases.generation_task_runner import GenerationTaskRunner

logger = logging.getLogger(__name__)


class TaskManager:
    """管理所有活跃的 GenerationTaskRunner 实例"""

    def __init__(self) -> None:
        self._runners: dict[str, GenerationTaskRunner] = {}

    def register(self, task_id: str, runner: GenerationTaskRunner) -> None:
        """注册 Runner"""
        self._runners[task_id] = runner
        logger.info("TaskManager: 注册 runner %s", task_id)

    def get(self, task_id: str) -> GenerationTaskRunner | None:
        """查找 Runner"""
        return self._runners.get(task_id)

    def remove(self, task_id: str) -> None:
        """移除 Runner"""
        self._runners.pop(task_id, None)
        logger.info("TaskManager: 移除 runner %s", task_id)
