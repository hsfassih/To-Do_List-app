import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

load_dotenv()

DATABASE_URL = os.getenv("database_url")
engine = create_async_engine(DATABASE_URL)

# DB AsyncSession Dependancy provider
async def get_db():
    db = AsyncSession(engine)
    try:
        yield db
    finally:
        await db.close()