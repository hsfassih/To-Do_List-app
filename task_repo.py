from tasks import Task
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

class TaskRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def make_task(self, task: Task) -> Task:
        self.session.add(task)
        await self.session.commit()
        await self.session.refresh(task)
        return task

    async def get_by_id(self, id: int) -> Task | None:
        stmt = select(Task).where(Task.id == id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def task_update(self, id: int, status: str) -> Task:
        task = await self.get_by_id(id)
        if not task:
            raise ValueError(f"Task of id {id} not found")
        task.task_status = status
        await self.session.commit()
        await self.session.refresh(task)
        return task

    async def dell_by_id(self, id: int) -> bool:
        task = await self.get_by_id(id)
        if not task:
            raise ValueError(f"Task of id {id} not found")
        await self.session.delete(task)
        await self.session.commit()
        return True