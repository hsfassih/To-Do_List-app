# imports from other files
from tasks import Task
from task_repo import TaskRepository
from users import User
from user_repo import UserRepo
from Authx2 import get_db, create_access_token, require_admin, get_current_user, engine, get_pswrd_hash, verify_pswrd
from request_utils import RegisterRequest, LoginRequest, UserRequest 
from initial_data import users_db, tasks_db

# python libraries/imports
import os, time, uuid, logging
from fastapi import FastAPI, HTTPException, APIRouter, Request, Response, Depends
from fastapi_redis_cache import FastApiRedisCache, cache
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware
from sqlmodel import SQLModel, select
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

# Request logging Middleware that logs the method, path, and response time for every request
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(levelname)s - %(message)s",
    force=True,     # prioritize this logger instead of using the default
    handlers=[
        # logging.StreamHandler(),    # defining stream to keep printing on terminal
        logging.FileHandler("app.log", encoding="utf-8")       # defining a file handler to write logfile
    ]
)
logger = logging.getLogger(__name__)

class RequestLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request:Request, call_next): # call_next is a callable for middleware functionality
        start_time = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start_time)*1000
        logger.info(
            f"{request.method} {request.url.path} "
            f"→ {response.status_code} | {duration_ms:.2f}ms"
        )
        return response

# Request ID middleware that attaches a unique "X-Request-ID" header to every response.
class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request:Request, call_next):
        response_id = str(uuid.uuid4())
        response = await call_next(request)
        response.headers["X-Request-ID"] = response_id
        return response

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
    repo = UserRepo(db_session)
    return await repo.get_all()

@router.post("/users/create") # admin endpoint
async def create_user(user:UserRequest, session:AsyncSession = Depends(get_db), current_user:User = Depends(require_admin)):
    repo = UserRepo(session)
    return await repo.add_user(user)

@router.put("/users/update{username}")
async def update_user(username:str, role:str, db_session:AsyncSession = Depends(get_db),  current_user:User = Depends(require_admin)):
    repo = UserRepo(db_session)
    return await repo.update_role(username, role)

@router.delete("/users/delete{username}")
async def delete_user(username:str, db_session:AsyncSession = Depends(get_db), current_user:User = Depends(require_admin)):
    repo = UserRepo(db_session)
    return await repo.delete_user(username)

@router.get("/tasks")
@cache(expire=30)
async def all_tasks(response:Response, db_session: AsyncSession = Depends(get_db)):
    repo = TaskRepository(db_session)
    return await repo.get_all()

@router.post("/tasks/create")
async def create_task(task:Task, db_session:AsyncSession = Depends(get_db)):
    repo = TaskRepository(db_session)
    return await repo.make_task(task)

@router.put("/tasks/update{id}") # protected endpoint
async def update_task(id:int, status:str, session:AsyncSession = Depends(get_db), current_user:User = Depends(get_current_user)):
    repo = TaskRepository(session)
    return await repo.task_update(id,status)

@router.delete("/tasks/delete{id}") # admin endpoint
async def delete_task(id:int, session:AsyncSession = Depends(get_db), current_user:User = Depends(require_admin)):
    repo = TaskRepository(session)
    return await repo.dell_by_id(id)

app.include_router(router)