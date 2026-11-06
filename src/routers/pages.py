from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.models import Post
from src.database import get_db

router = APIRouter(
    tags=["pages"],
    include_in_schema=False
)

templates = Jinja2Templates(directory="src/templates")



@router.get("/", name="home")
async def home_page(request: Request, db: AsyncSession = Depends(get_db)):
    query = (
        select(Post)
        .options(
            selectinload(Post.author)
        )
        .order_by(Post.id.desc())
        .limit(4)
    )
    result = await db.execute(query)
    posts = result.scalars().all()

    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context={
            "request": request,
            "posts": posts,
            "total_posts": len(posts)
        }
    )

@router.get("/posts", status_code=status.HTTP_200_OK)
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

@router.get("/posts/{post_id}")
async def post_detail(
    post_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db)
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


@router.get("/create-account", name="create_account_page")
async def create_account_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="createcont.html",
        context={
            "request": request,
        },
    )


@router.get("/account", name="account_management_page")
async def account_management_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="account_management.html",
        context={
            "request": request,
        },
    )


@router.get("/account/password", name="account_password_page")
async def account_password_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="account_password.html",
        context={
            "request": request,
        },
    )