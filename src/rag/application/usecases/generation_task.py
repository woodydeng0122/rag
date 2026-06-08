import asyncio
import logging

from rag.application.task_manager import TaskManager
from rag.domain.entities.generation_task import GenerationTask, TaskStatus
from rag.domain.ports.generation_task_repository import GenerationTaskRepositoryPort

logger = logging.getLogger(__name__)


class GenerationTaskUseCase:
    """生成任务的查询与生命周期控制"""

    def __init__(self, task_repo: GenerationTaskRepositoryPort):
        self.task_repo = task_repo

    async def list_tasks(self, project_id: str) -> list[GenerationTask]:
        """查询项目的生成任务列表"""
        return await self.task_repo.list_by_project(project_id)

    async def get_task(self, task_id: str) -> GenerationTask | None:
        """查询单个生成任务"""
        return await self.task_repo.get_by_id(task_id)

    async def pause_task(self, task_id: str, task_manager: TaskManager) -> None:
        """暂停生成任务"""
        task = await self.task_repo.get_by_id(task_id)
        if task is None:
            raise ValueError(f"生成任务 {task_id} 不存在")
        if task.status != TaskStatus.RUNNING:
            raise ValueError(f"无法暂停状态为 {task.status.value} 的任务")

        runner = task_manager.get(task_id)
        if runner:
            runner.pause_event.clear()

        task.pause()
        await self.task_repo.update(task)

    async def resume_task(self, task_id: str, task_manager: TaskManager) -> None:
        """继续生成任务"""
        task = await self.task_repo.get_by_id(task_id)
        if task is None:
            raise ValueError(f"生成任务 {task_id} 不存在")
        if task.status != TaskStatus.PAUSED:
            raise ValueError(f"无法继续状态为 {task.status.value} 的任务")

        runner = task_manager.get(task_id)
        if runner:
            runner.pause_event.set()

        task.resume()
        await self.task_repo.update(task)

    async def cancel_task(self, task_id: str, task_manager: TaskManager) -> None:
        """取消生成任务"""
        task = await self.task_repo.get_by_id(task_id)
        if task is None:
            raise ValueError(f"生成任务 {task_id} 不存在")
        if task.status not in (TaskStatus.RUNNING, TaskStatus.PAUSED):
            raise ValueError(f"无法取消状态为 {task.status.value} 的任务")

        runner = task_manager.get(task_id)
        if runner:
            runner.cancel_flag.set()
            if task.status == TaskStatus.PAUSED:
                runner.pause_event.set()

        task.cancel()
        await self.task_repo.update(task)
        task_manager.remove(task_id)

    async def retry_failed_task(self, task_id: str, task_manager: TaskManager) -> int:
        """重试失败项，返回重试数量"""
        task = await self.task_repo.get_by_id(task_id)
        if task is None:
            raise ValueError(f"生成任务 {task_id} 不存在")
        if task.status not in (TaskStatus.COMPLETED, TaskStatus.CANCELLED):
            raise ValueError("只能重试已完成或已取消的任务")

        runner = task_manager.get(task_id)
        if runner is None or not runner.failed_items:
            raise ValueError("没有失败项可重试")

        retry_count = len(runner.failed_items)

        # 恢复任务状态为 running
        task.status = TaskStatus.RUNNING
        await self.task_repo.update(task)

        # 重新注册 Runner 并启动重试
        task_manager.register(task_id, runner)
        runner.pause_event.set()
        runner.cancel_flag.clear()

        async def _retry_and_cleanup():
            try:
                await runner.retry_failed()
            finally:
                task_manager.remove(task_id)

        asyncio.create_task(_retry_and_cleanup())

        return retry_count
