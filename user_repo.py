from users import User
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from Authx2 import get_pswrd_hash

class UserRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_user(self, id: int, username: str, pswrd: str, role: str | None) -> User:
        hashed_pswrd = get_pswrd_hash(pswrd)
        user = User(id=id, username=username, hashed_pswrd=hashed_pswrd, role=role)
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def get_by_username(self, username: str) -> User | None:
        stmt = select(User).where(User.username == username)
        result = await self.session.execute(stmt)
        return result.scalars().first()             