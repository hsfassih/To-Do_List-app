from pydantic import BaseModel, Field

# Request Utilities
class UserRequest(BaseModel):
    # id:int
    username:str
    plain_pswrd:str
    role:str = Field(default="user")

class RegisterRequest(BaseModel):
    # id:int = Field(default=None, primary_key=True)
    username:str
    plain_pswrd:str
    role:str

class LoginRequest(BaseModel):
    # id:int
    username:str
    plain_pswrd:str
    role:str