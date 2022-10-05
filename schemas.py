from pydantic import BaseModel
from typing import Optional, List, Dict

class ProblemBase(BaseModel):
    text:str

class Problem(ProblemBase):
    id:int
    user_id:int
    class Config:
        orm_mode = True

class ProblemCreate(ProblemBase):
    pass

class UserBase(BaseModel):
    username:str
    email:str
    first_name:str
    last_name:str
    password:str
    date_joined:str
    last_login: Optional[str] = None
    is_superuser:int = 0
    is_staff:int = 0
    is_active:int = 1

class User(UserBase):
    id:int
    class Config:
        orm_mode = True

class UserCreate(UserBase):
    pass