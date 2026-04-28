from sqlmodel import SQLModel, Field
from typing import Optional


# defining user class with repo architecture
class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None)
    full_name: str
    username: str = Field(unique=True, primary_key=True)
    hashed_pswrd: str
    role: str = Field(default="user")
