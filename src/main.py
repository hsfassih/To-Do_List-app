# imports from other files
from tasks import Task
from task_repo import TaskRepository
from users import User
from user_repo import UserRepo
from Authx2 import get_db, require_admin, get_current_user, engine, get_pswrd_hash
from request_utils import RegisterRequest, LoginRequest, UserRequest 
from middleware import RequestIDMiddleware, RequestLogMiddleware
from initial_data import users_db, tasks_db
from user_service import UserService
from task_service import TaskService

# python libraries/imports
import os
from fastapi import FastAPI, APIRouter, Request, Response, Depends
from fastapi_redis_cache import FastApiRedisCache, cache
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