from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

import src.models.user as user
from src.database import get_db

from src.schemas.schemas import PostResponse, PostCreate, PostUpdate, Token, UserUpdate
from src.auth import oauth2_scheme, verify_access_token

router = APIRouter(
  prefix="/posts",
  tags=["posts"],
)

@router.post("/create", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(
  post: PostCreate,
  db: AsyncSession = Depends(get_db),
  token: str = Depends(oauth2_scheme)
):

    user_id = verify_access_token(token)

    new_post = user.Post(**post.model_dump(), user_id=int(user_id))

    db.add(new_post)
    await db.commit()
    await db.refresh(new_post)

    return new_post


@router.get("/{post_id}", response_model=PostResponse)
async def get_post(post_id: int, db: AsyncSession = Depends(get_db)):

    query = select(user.Post).where(user.Post.id == post_id)

    result = await db.execute(query)
    post = result.scalars().first()

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found!"
        )

    return post


@router.get("/", response_model=list[PostResponse])
async def get_all_posts(db: AsyncSession = Depends(get_db)):

    query = select(user.Post)

    result = await db.execute(query)

    posts = result.scalars().all()

    return posts


@router.patch("/{post_id}", response_model=PostResponse)
async def update_post(
  post_id: int,
  post_update: PostUpdate,
  db: AsyncSession = Depends(get_db),
  token: str = Depends(oauth2_scheme)
):

    current_user_id = verify_access_token(token)

    query = select(user.Post).where(user.Post.id == post_id)
    result = await db.execute(query)
    db_post = result.scalars().first()

    if not db_post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )

    if str(db_post.user_id) != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to perform requested action"
        )

    update_data = post_update.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(db_post, key, value)

    await db.commit()
    await db.refresh(db_post)

    return db_post


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: int,
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):

    current_user_id = verify_access_token(token)

    query = select(user.Post).where(user.Post.id == post_id)
    result = await db.execute(query)
    db_post = result.scalars().first()

    if not db_post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found!"
        )

    if str(db_post.user_id) != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to delete this post"
        )

    await db.delete(db_post)
    await db.commit()