import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

load_dotenv()

# Resolve project root regardless of where uvicorn is launched from:
# src/auth/database.py → parent = src/auth → parent = src → parent = project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DB_NAME = "todo_list.db"
DATABASE_URL = f"sqlite+aiosqlite:///{PROJECT_ROOT / DB_NAME}"
engine = create_async_engine(DATABASE_URL)

# DB AsyncSession Dependancy provider
async def get_db():
    db = AsyncSession(engine)
    try:
        yield db
    finally:
        await db.close()