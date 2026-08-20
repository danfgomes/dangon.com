from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.models.post import Post, Comment
from src.schemas.comment import CommentCreate, CommentResponse
from src.database import AsyncSession, get_db
from src.auth import get_current_user


router = APIRouter(
    prefix="/posts",
    tags=["comments"],
)


@router.post("/{post_id}/comments", response_model=CommentResponse)
async def create_comment(
    post_id: int,
    comment: CommentCreate,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user),
):

    query = select(Post.id).where(Post.id == post_id)

    result_cursor = await db.execute(query)

    result = result_cursor.scalar_one_or_none()

    if not result:
        raise HTTPException(status_code=404, detail="Post not found")

    new_comment = Comment(
        post_id=post_id, author_id=current_user_id, **comment.model_dump()
    )
    db.add(new_comment)
    await db.commit()
    await db.refresh(new_comment)
    return new_comment

@router.get("/{post_id}/comments/{comment_id}", response_model=CommentResponse)
async def get_comment(
    post_id: int,
    comment_id: int,
    db: AsyncSession = Depends(get_db)
):
    query = (select(Post).options(selectinload(Post.id)))
    result_cursor = (await db.execute(query)).scalar_one_or_none()


    return result_cursor

