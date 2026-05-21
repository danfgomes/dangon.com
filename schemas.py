from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional

class User(BaseModel):
    name: str
    email: str
    id: int

class User_response(BaseModel):
    name: str
    email: str
    id: int
    message: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None

class UserDeleteResponse(BaseModel):
    message: str

class Post(BaseModel):
    title: str
    content: str
    id: int

class PostResponse(BaseModel):
    title: str
    content: str
    id: int
    message: str


class PostDeleteResponse(BaseModel):
    message: str

class UpdatePost(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None

