from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.auth import get_admin_user
from src.database import get_db
from src.models import Post, User
from src.schemas.post import (
    PaginatedPostsResponse,
    PostCreate,
    PostResponse,
    PostUpdate,
)

router = APIRouter(
    prefix="/api/posts",
    tags=["posts"],
)


@router.post("/", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(
    post: PostCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    new_post = Post(**post.model_dump(), author_id=current_user.id)
    db.add(new_post)
    await db.commit()

    query = (
        select(Post).options(selectinload(Post.author)).where(Post.id == new_post.id)
    )
    result = await db.execute(query)
    created_post = result.scalars().first()

    return created_post


@router.get("/", response_model=PaginatedPostsResponse, status_code=status.HTTP_200_OK)
async def list_posts_api(
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
):
    count_result = await db.execute(select(func.count()).select_from(Post))
    total = count_result.scalar() or 0

    posts_query = (
        select(Post)
        .options(selectinload(Post.author))
        .order_by(Post.id.desc())
        .limit(limit)
        .offset(skip)
    )

    result = await db.execute(posts_query)
    db_posts = result.scalars().all()

    # Converte cada modelo do SQLAlchemy (Post) para o Pydantic (PostResponse)
    posts = [PostResponse.model_validate(post) for post in db_posts]

    return PaginatedPostsResponse(
        posts=posts,
        total=total,
        skip=skip,
        limit=limit,
        has_more=(skip + limit) < total,
    )


@router.get("/{post_id}", response_model=PostResponse, status_code=status.HTTP_200_OK)
async def get_post_api(post_id: int, db: AsyncSession = Depends(get_db)):
    query = select(Post).options(selectinload(Post.author)).where(Post.id == post_id)
    result = await db.execute(query)
    post = result.scalars().first()

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found!"
        )

    return post


@router.patch("/{post_id}", response_model=PostResponse)
async def update_post(
    post_id: int,
    post_update: PostUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    query = select(Post).options(selectinload(Post.author)).where(Post.id == post_id)
    result = await db.execute(query)
    db_post = result.scalars().first()

    if not db_post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )

    if db_post.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to perform requested action",
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
    current_user: User = Depends(get_admin_user),
):
    query = select(Post).where(Post.id == post_id)
    result = await db.execute(query)
    db_post = result.scalars().first()

    if not db_post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found!"
        )

    if db_post.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to delete this post",
        )

    await db.delete(db_post)
    await db.commit()
