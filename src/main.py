# imports from other files
from tasks.models import Task
from tasks.repository import TaskRepository
from users.models import User
from users.repository import UserRepo
from auth.dependancies import require_admin, get_current_user
from auth.database import get_db, engine
from auth.utils import get_pswrd_hash
from auth.schemas import RegisterRequest, LoginRequest, UserRequest 
from middleware import RequestIDMiddleware, RequestLogMiddleware
from seed.initial_data import users_db, tasks_db
from users.service import UserService
from tasks.service import TaskService
from config import settings

# python libraries/imports
import os
from fastapi import FastAPI, APIRouter, Request, Response, Depends
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache
from redis import asyncio as aioredis
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from sqlmodel import SQLModel
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager

LOCAL_REDIS_URL = os.getenv("local_redis_url")

limiter = Limiter(key_func=get_remote_address)

# initialize database on every application startup
@asynccontextmanager
async def lifespan(app:FastAPI):
    # redis cache initialization on startup
    redis = aioredis.from_url(settings.redis_url)
    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")
    print(f"Redis cache initialized | {settings.redis_url}")
    
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
                    full_name=user["full_name"],
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

app.add_middleware(RequestLogMiddleware)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # all origins allowed in development
    allow_credentials=False,   # must be False when allow_origins=["*"]
    allow_methods=["*"],
    allow_headers=["*"],
)


# Non-Functinoal Endpoints (for Authentication & Authorization)
@router.post("/auth/register")
async def register(data:RegisterRequest, session:AsyncSession = Depends(get_db)):
    service = UserService(UserRepo(session))
    return await service.register(data)

@router.post("/auth/login")
async def login(data:LoginRequest, session:AsyncSession = Depends(get_db)):
    service = UserService(UserRepo(session))
    return await service.login(data)

# Functional Endpoints
@router.get("/")
async def home_page():
    return {
        "home page": "hello world"
    }

# user routes

@router.get("/users")
@limiter.limit("5/minute")
async def all_users(request:Request, db_session: AsyncSession = Depends(get_db)):
    service = UserService(UserRepo(db_session))
    return await service.get_all_users()

@router.post("/users/create") # admin endpoint
async def create_user(user:UserRequest, db_session:AsyncSession = Depends(get_db), current_user:User = Depends(require_admin)):
    service = UserService(UserRepo(db_session))
    return await service.create_user(user)

@router.put("/users/update{username}")
async def update_user(username:str, role:str, db_session:AsyncSession = Depends(get_db),  current_user:User = Depends(require_admin)):
    service = UserService(UserRepo(db_session))
    return await service.update_user_role(username, role)

@router.delete("/users/delete{username}")
async def delete_user(username:str, db_session:AsyncSession = Depends(get_db), current_user:User = Depends(require_admin)):
    service = UserService(UserRepo(db_session))
    return await service.delete_user(username)

# Task routes

@router.get("/tasks")
@cache(expire=30)
async def all_tasks(response:Response, db_session: AsyncSession = Depends(get_db)):
    service = TaskService(TaskRepository(db_session))
    return await service.get_all_tasks()

@router.post("/tasks/create")
async def create_task(task:Task, db_session:AsyncSession = Depends(get_db)):
    service = TaskService(TaskRepository(db_session))
    return await service.create_task(task)

@router.put("/tasks/update{id}") # protected endpoint
async def update_task(id:int, status:str, db_session:AsyncSession = Depends(get_db), current_user:User = Depends(get_current_user)):
    service = TaskService(TaskRepository(db_session))
    return await service.update_task_status(id, status)

@router.delete("/tasks/delete{id}") # admin endpoint
async def delete_task(id:int, db_session:AsyncSession = Depends(get_db), current_user:User = Depends(require_admin)):
    service = TaskService(TaskRepository(db_session))
    return await service.delete_task(id)

app.include_router(router)

# comment for changes ()