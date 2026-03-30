from sqlmodel import SQLModel, Field

# defining user class with repo architecture
class User(SQLModel, table=True):
    id:int = Field(default=None)
    username:str = Field(primary_key=True)
    hashed_pswrd:str
    role:str = Field(default="user")
