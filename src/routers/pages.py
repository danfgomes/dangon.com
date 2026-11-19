from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.config import settings
from src.database import get_db
from src.models import Post

router = APIRouter(tags=["pages"], include_in_schema=False)

templates = Jinja2Templates(directory="src/templates")


@router.get("/", name="home")
async def home_page(request: Request, db: AsyncSession = Depends(get_db)):
    query = (
        select(Post)
        .options(selectinload(Post.author))
        .order_by(Post.id.desc())
        .limit(4)
    )
    result = await db.execute(query)
    posts = result.scalars().all()

    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context={"request": request, "posts": posts, "total_posts": len(posts)},
    )


@router.get("/posts", status_code=status.HTTP_200_OK)
async def list_all_posts(
    request: Request,
    db: AsyncSession = Depends(get_db),
):

    count_result = await db.execute(select(func.count()).select_from(Post))
    total = count_result.scalar() or 0

    result = await db.execute(
        select(Post)
        .options(selectinload(Post.author))
        .order_by(Post.date_posted.desc())
        .limit(settings.posts_per_page),
    )

    posts = result.scalars().all()

    has_more = len(posts) < total

    return templates.TemplateResponse(
        request=request,
        name="posthome.html",
        context={
            "posts": posts,
            "limit": settings.posts_per_page,
            "has_more": has_more,
        },
    )


@router.get("/posts/{post_id}")
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


@router.get("/create-account", name="create_account_page")
async def create_account_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="createcont.html",
        context={
            "request": request,
        },
    )


@router.get("/forgot-password", include_in_schema=False)
async def forgot_password_page(request: Request):
    return templates.TemplateResponse(
        request,
        "forgot_password.html",
        {"title": "Forgot Password"},
    )


@router.get("/reset-password", include_in_schema=False)
async def reset_password_page(request: Request):
    response = templates.TemplateResponse(
        request,
        "reset_password.html",
        {"title": "Reset Password"},
    )
    response.headers["Referrer-policy"] = "no-referrer"
    return response


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
