from tasks.repository import TaskRepository
from tasks.models import Task
from fastapi import HTTPException

VALID_STATUSES = {"pending", "in progress", "done"}


class TaskService:
    def __init__(self, repo: TaskRepository):
        self.repo = repo

    async def get_all_tasks(self) -> list[Task]:
        return await self.repo.get_all()

    async def get_task(self, id: int) -> Task:
        task = await self.repo.get_by_id(id)
        if not task:
            raise HTTPException(status_code=404, detail=f"Task {id} not found")
        return task

    async def create_task(self, task: Task) -> Task:
        if task.task_status not in VALID_STATUSES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. You must Choose from {VALID_STATUSES}",
            )
        return await self.repo.make_task(task)

    async def update_task_status(self, id: int, status: str) -> Task:
        if status not in VALID_STATUSES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. You must Choose from {VALID_STATUSES}",
            )

        task = await self.repo.get_by_id(id)
        if not task:
            raise HTTPException(status_code=404, detail=f"Task {id} not found")

        # custom business rule: a completed task cannot be modified
        if task.task_status == "done":
            raise HTTPException(
                status_code=409, detail="A task marked as 'done' cannot be updated"
            )

        return await self.repo.task_update(id, status)

    async def delete_task(self, id: int) -> bool:
        task = await self.repo.get_by_id(id)
        if not task:
            raise HTTPException(status_code=404, detail=f"Task {id} not found")
        return await self.repo.dell_by_id(id)
