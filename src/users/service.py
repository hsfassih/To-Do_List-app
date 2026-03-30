from fastapi import HTTPException

from users.repository import UserRepo
from users.models import User
from auth.schemas import RegisterRequest, LoginRequest, UserRequest
from auth.utils import create_access_token, verify_pswrd

class UserService:
    def __init__(self, repo: UserRepo):
        self.repo = repo

    async def register(self, data: RegisterRequest) -> dict:
        existing = await self.repo.get_by_username(data.username)
        if existing:
            raise HTTPException(status_code=400, detail="User already exists")
        user = await self.repo.add_user(data)
        access_token = create_access_token(data={"sub": user.username})
        return {"access_token": access_token, "token_type": "bearer"}

    async def login(self, data: LoginRequest) -> dict:
        user = await self.repo.get_by_username(data.username)
        if not user or not verify_pswrd(data.plain_pswrd, user.hashed_pswrd):
            raise HTTPException(status_code=401, detail="Incorrect username or password")
        access_token = create_access_token(data={"sub": user.username})
        return {"access_token": access_token, "token_type": "bearer"}

    async def get_all_users(self) -> list[User]:
        return await self.repo.get_all()

    async def create_user(self, user: UserRequest) -> User:
        existing = await self.repo.get_by_username(user.username)
        if existing:
            raise HTTPException(status_code=400, detail="User already exists")
        return await self.repo.add_user(user)

    async def update_user_role(self, username: str, role: str) -> User:
        user = await self.repo.get_by_username(username)
        if not user:
            raise HTTPException(status_code=404, detail=f"User '{username}' not found")
        allowed_roles = {"user", "admin"}
        if role not in allowed_roles:
            raise HTTPException(status_code=400, detail=f"Invalid role. Choose from {allowed_roles}")
        return await self.repo.update_role(username, role)

    async def delete_user(self, username: str) -> bool:
        user = await self.repo.get_by_username(username)
        if not user:
            raise HTTPException(status_code=404, detail=f"User '{username}' not found")
        return await self.repo.delete_user(username)