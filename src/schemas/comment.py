from datetime import datetime

from pydantic import BaseModel, Field

from .user import UserPublic


class CommentCreate(BaseModel):
    content: str = Field(min_length=1, max_length=2000)


class CommentUpdate(CommentCreate):
    pass


class CommentResponse(CommentCreate):
    id: int
    author: UserPublic | None
    post_id: int
    date_posted: datetime

