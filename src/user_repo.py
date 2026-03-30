from users import User
from request_utils import UserRequest
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from Authx2 import get_pswrd_hash

class UserRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_user(self, user:UserRequest) -> User:
        user = User(full_name=user.full_name, username=user.username, hashed_pswrd=get_pswrd_hash(user.plain_pswrd), role=user.role)
        self.session.add(user)
        await self.session.commit()
        return user

    async def get_all(self) -> list[User]:
        statement = select(User)
        result = await self.session.execute(statement)
        users = result.scalars().all()
        if not users:
            return {"message": "No users found"}
        return users

    async def get_by_username(self, username: str) -> User | None:
        user = await self.session.get(User, username)
        return user

    async def update_role(self, username:str, role:str) -> User | None:
        user = await self.get_by_username(username)
        user.role = role
        await self.session.commit()
        await self.session.refresh(user)
        return user
    
    async def delete_user(self, username:str) -> bool:
        try:
            await self.session.delete(User, username)
            await self.session.commit()
        except:
            return None
            # return ValueError("The user does not exist")
        return True
    