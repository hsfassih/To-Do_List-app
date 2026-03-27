import os
from dotenv import load_dotenv
from users import User
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from pwdlib import PasswordHash

load_dotenv()

SECRET_KEY = os.getenv("secret_key")
ALGORITHM = os.getenv("algorithm")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("access_token_expire_minutes", 30))
DATABASE_URL = os.getenv("database_url")

engine = create_async_engine(DATABASE_URL)

# DB AsyncSession Dependancy provider
async def get_db():
    db = AsyncSession(engine)
    try:
        yield db
    finally:
        await db.close()

#utilities for password hashing
password_hash = PasswordHash.recommended()
def verify_pswrd(plain_password, hashed_password):
    return password_hash.verify(plain_password, hashed_password)

def get_pswrd_hash(password):
    return password_hash.hash(password)

# utilities for JWT
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token:str) -> str | None:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            return None
        return username
    except JWTError:
        return None


# utilities for authorization
security = HTTPBearer()

async def get_current_user(credentials:HTTPAuthorizationCredentials = Depends(security), session:AsyncSession = Depends(get_db)) -> User:
    token = credentials.credentials
    username = verify_token(token)
    if username is None:
        raise HTTPException(status_code=401, detail="Invalid Token")
    
    # fetch user from the database
    stmt = select(User).where(User.username == username)
    result = await session.execute(stmt)
    user = result.scalars().first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user

async def require_admin(crnt_user:User = Depends(get_current_user)) -> User: # already depends on logged in user
    if crnt_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return crnt_user