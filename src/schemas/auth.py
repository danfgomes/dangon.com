from pydantic import BaseModel
from typing import TypedDict


class Token(BaseModel):
    access_token: str
    token_type: str
#/posts/create_post_posts_create_post

class TokenPayload(TypedDict):
    sub: str
    role: str
