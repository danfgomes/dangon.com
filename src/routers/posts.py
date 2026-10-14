from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    Query,
    Request,
)  # Import do Request adicionado
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func  # Import do func adicionado
from sqlalchemy.orm import selectinload

from src.models import User, Post
from src.database import get_db

from src.schemas.post import PostCreate, PostResponse, PostUpdate
from src.auth import (
    oauth2_scheme,
    get_current_user,
    get_admin_user,
)

router = APIRouter(
    prefix="/posts",
    tags=["posts"],
)

templates = Jinja2Templates(directory="src/templates")


@router.post(
    "/create", response_model=PostResponse, status_code=status.HTTP_201_CREATED
)
async def create_post(
    post: PostCreate,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_admin_user),
):

    new_post = Post(**post.model_dump(), author_id=current_user_id)

    db.add(new_post)
    await db.commit()

    query = (
        select(Post).options(selectinload(Post.author)).where(Post.id == new_post.id)
    )

    result = await db.execute(query)
    created_post = result.scalars().first()
    await db.commit()

    return created_post


@router.get("/recent")
async def home(
    request: Request,
    limit: int = Query(default=5, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):

    total_result = await db.execute(select(func.count(Post.id)))
    total_posts = total_result.scalar() or 0

    posts_query = (
        select(Post)
        .options(selectinload(Post.author))
        .order_by(Post.id.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(posts_query)
    posts = result.scalars().all()

    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context={
            "posts": posts,
            "total_posts": total_posts,
        },
    )


@router.get("/", status_code=status.HTTP_200_OK)
async def list_all_posts(
    request: Request,
    limit: int = Query(default=10, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    posts_query = (
        select(Post)
        .options(selectinload(Post.author))
        .order_by(Post.id.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(posts_query)
    posts = result.scalars().all()

    return templates.TemplateResponse(
        request=request,
        name="posthome.html",
        context={
            "posts": posts,
        },
    )


@router.get("/{post_id}")
async def post_detail(
    post_id: int, request: Request, db: AsyncSession = Depends(get_db)
):

    query = select(Post).options(selectinload(Post.author)).where(Post.id == post_id)

    result = await db.execute(query)
    post = result.scalars().first()

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found!"
        )

    return templates.TemplateResponse(
        request=request,
        name="post_detail.html",
        context={
            "post": post,
        },
    )


@router.patch("/{post_id}", response_model=PostResponse)
async def update_post(
    post_id: int,
    post_update: PostUpdate,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user),
):
    query = select(Post).options(selectinload(Post.author)).where(Post.id == post_id)
    result = await db.execute(query)
    db_post = result.scalars().first()

    if not db_post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )

    if (db_post.author_id) != user_id:
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
    user_id: int = Depends(get_current_user),
):

    query = select(Post).where(Post.id == post_id)
    result = await db.execute(query)
    db_post = result.scalars().first()

    if not db_post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found!"
        )

    if (db_post.author_id) != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to delete this post",
        )

    await db.delete(db_post)
    await db.commit()
