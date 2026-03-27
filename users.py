from sqlmodel import SQLModel, Field

# defining user class with repo architecture
class User(SQLModel, table=True):
    id:int = Field(default=None, primary_key=True)
    username:str
    hashed_pswrd:str
    role:str = Field(default="user")
