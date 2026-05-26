from datetime import datetime

from pydantic import BaseModel, Field, EmailStr, ConfigDict


class UserBase(BaseModel):
    username: str = Field(min_length=1, max_length=255)
    email: EmailStr = Field(min_length=1, max_length=150)


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=255)


class UserPublic(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    image_file: str | None
    image_path: str


class UserPrivate(UserPublic):
    email: EmailStr


class UserUpdate(BaseModel):
    username: str | None = Field(default=None, min_length=1, max_length=255)
    email: EmailStr | None = Field(default=None, min_length=1, max_length=150)
    image_file: str | None = Field(default=None, min_length=1, max_length=255)


class Token(BaseModel):
    access_token: str
    token_type: str


class PostBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=1, max_length=2000)


class PostCreate(PostBase):
    id: int


class PostUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    content: str | None = Field(default=None, min_length=1, max_length=2000)


class PostResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    content: str
    date_posted: datetime
    author_id: int
    author: UserPublic | None
