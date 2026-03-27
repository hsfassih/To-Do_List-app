from tasks import Task
from task_repo import TaskRepository
from users import User
from user_repo import UserRepo
from Authx2 import get_db, create_access_token, require_admin, get_current_user, engine, get_pswrd_hash, verify_pswrd
from request_utils import RegisterRequest, LoginRequest, UserRequest 
from initial_data import users_db, tasks_db

import os
from fastapi import FastAPI, HTTPException, APIRouter, Request, Response, Depends
from fastapi_redis_cache import FastApiRedisCache, cache
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from sqlmodel import SQLModel, Field, select
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager

LOCAL_REDIS_URL = os.getenv("local_redis_url")

limiter = Limiter(key_func=get_remote_address)

# initialize database on every application startup
@asynccontextmanager
async def lifespan(app:FastAPI):
    # redis cache initialization on startup
    redis_cache = FastApiRedisCache()
    redis_cache.init(
        host_url=os.environ.get("REDIS_URL", LOCAL_REDIS_URL)
    )
    
    # inspect using run_sync to bridge async → sync
    async with engine.connect() as conn:
        existing_tables = await conn.run_sync(lambda sync_conn: inspect(sync_conn).get_table_names())

    if not existing_tables or "user" not in existing_tables or "task" not in existing_tables:
        # create_all also needs run_sync to bridge
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

        async with AsyncSession(engine) as startup_session:
            for user in users_db:
                user = User(
                    id=user["id"],
                    username=user["username"],
                    hashed_pswrd= get_pswrd_hash(user["password"]),
                    role=user["role"]
                )
                startup_session.add(user)
            for task in tasks_db:
                task = Task(
                    id=task["id"],
                    assigner=task["assigner"],
                    assignee=task["assignee"],
                    detail=task["detail"],
                    task_status=task["task_status"]
                )
                startup_session.add(task)
            await startup_session.commit()
        print("Harcoded entries added")
    else:
        print("both tables already exist")

    yield # necessary

router = APIRouter(prefix="/api/v1")
app = FastAPI(lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Non-Functinoal Endpoints (for Authentication & Authorization)
@router.post("/auth/register")
async def register(data:RegisterRequest, session:AsyncSession = Depends(get_db)):
    user_repo = UserRepo(session)
    existing = await user_repo.get_by_username(data.username)
    if existing:
        raise HTTPException(status_code=400, detail="User already exits")
    user = await user_repo.add_user(data.username, data.plain_pswrd, data.role)
    access_token = create_access_token(data={"sub":user.username})
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }
    
@router.post("/auth/login")
async def login(data:LoginRequest, session:AsyncSession = Depends(get_db)):
    user_repo = UserRepo(session)
    user = await user_repo.get_by_username(data.username)
    if not user or not verify_pswrd(data.plain_pswrd, user.hashed_pswrd):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub":user.username})
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }
    
# Functional Endpoints
@router.get("/")
async def home_page():
    return {
        "home page": "hello world"
    }

@router.get("/users")
@limiter.limit("5/minute")
async def all_users(request:Request, db_session: AsyncSession = Depends(get_db)):
    stmt = select(User)
    result = await db_session.execute(stmt)
    users = result.scalars().all()
    if not users:
        return {"message": "No users found"}
    return users

@router.get("/tasks")
@cache(expire=30)
async def all_tasks(response:Response, db_session: AsyncSession = Depends(get_db)):
    stmt = select(Task)
    result = await db_session.execute(stmt)
    tasks = result.scalars().all()
    if not tasks:
        return {"message": "No tasks found"}
    return [task.model_dump() for task in tasks] # returning dumps of singular task items

@router.post("/create_user") # admin endpoint
async def create_user(user:UserRequest, session:AsyncSession = Depends(get_db), crnt_user:User = Depends(require_admin)):
    repo = UserRepo(session)
    return await repo.add_user(user.id, user.username, user.plain_pswrd, user.role)

@router.post("/create_task")
async def create_task(task:Task, session:AsyncSession = Depends(get_db)):
    repo = TaskRepository(session)
    return await repo.make_task(task)

@router.put("/task_update") # protected endpoint
async def update_task(id:int, status:str, session:AsyncSession = Depends(get_db), crnt_user:User = Depends(get_current_user)):
    repo = TaskRepository(session)
    return await repo.task_update(id,status)

@router.delete("/del_task") # admin endpoint
async def delete_task(id:int, session:AsyncSession = Depends(get_db), crnt_user:User = Depends(require_admin)):
    repo = TaskRepository(session)
    return await repo.dell_by_id(id)

app.include_router(router)