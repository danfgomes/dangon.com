from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, Response, UploadFile, status
from typing import Annotated
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordRequestForm

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func, select
from PIL import UnidentifiedImageError
from starlette.concurrency import run_in_threadpool

from image_utils import delete_profile_image, process_profile_image

from src.auth import (
    authenticate_user,
    create_access_token,
    get_current_user,
    hash_password,
)
from src.config import settings
from src.database import get_db
from src.models.user import User
from src.schemas.auth import Token
from src.schemas.user import UserCreate, UserPrivate, UserPublic, UserUpdate


router = APIRouter(
    prefix="/api/users",
    tags=["users"],
)

legacy_router = APIRouter(
    prefix="/users",
    tags=["legacy-users"],
)

templates = Jinja2Templates(directory="src/templates")


@legacy_router.post("/create", response_model=UserPrivate, status_code=status.HTTP_200_OK)
async def legacy_create_user(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    result_user = await db.execute(
        select(User).where(func.lower(User.username) == user_in.username.lower())
    )
    if result_user.scalars().first():
        raise HTTPException(status_code=400, detail="Username already exists")

    result_email = await db.execute(
        select(User).where(func.lower(User.email) == user_in.email.lower())
    )
    if result_email.scalars().first():
        raise HTTPException(status_code=400, detail="Email already registered")

    db_user = User(
        username=user_in.username,
        email=user_in.email,
        password=hash_password(user_in.password),
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


@legacy_router.post("/login")
async def legacy_login_user(
    response: Response,
    email: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    user = await authenticate_user(db, email, password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    token = create_access_token({"sub": str(user.id), "role": getattr(user, "role", "user")})
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        path="/",
    )
    return RedirectResponse(url="/", status_code=302)


@router.post("/create", response_model=UserPrivate, status_code=status.HTTP_201_CREATED)
async def create_user(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    result_user = await db.execute(
        select(User).where(func.lower(User.username) == user_in.username.lower())
    )
    if result_user.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists",
        )

    result_email = await db.execute(
        select(User).where(func.lower(User.email) == user_in.email.lower())
    )
    if result_email.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    hashed_password = hash_password(user_in.password)
    db_user = User(
        **user_in.model_dump(exclude={"password"}),
        password=hashed_password,
    )

    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: AsyncSession = Depends(get_db),
):
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    role = getattr(user, "role", "user")
    access_token = create_access_token(data={"sub": str(user.id), "role": role})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserPrivate)
async def get_current_user_in(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/{user_id}", response_model=UserPrivate)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access blocked. The resource belongs to another account.",
        )

    update_data = user_update.model_dump(exclude_unset=True)

    if "password" in update_data:
        update_data["password"] = hash_password(update_data["password"])

    for key, value in update_data.items():
        setattr(current_user, key, value)

    try:
        db.add(current_user)
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Dado inoperante!"
        )

    await db.refresh(current_user)
    return current_user


@router.get("/{user_id}", response_model=UserPublic)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
):
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access blocked. The resource belongs to another account.",
        )
    return current_user


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    old_filename = current_user.image_file

    await db.delete(current_user)
    await db.commit()

    if old_filename:
        delete_profile_image(old_filename)


@router.patch("/{user_id}/picture", response_model=UserPrivate)
async def upload_profile_picture(
    user_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this user's picture",
        )

    content = await file.read()
    max_size_mb = settings.max_upload_size_bytes // (1024 * 1024)
    if len(content) > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size is {max_size_mb}MB",
        )

    try:
        new_filename = await run_in_threadpool(process_profile_image, content)
    except UnidentifiedImageError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image file. Please upload a valid image (JPEG, PNG, GIF, WebP).",
        ) from err

    old_filename = current_user.image_file
    current_user.image_file = new_filename
    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)

    if old_filename:
        delete_profile_image(old_filename)

    return current_user


@router.delete("/{user_id}/picture", response_model=UserPrivate)
async def delete_user_picture(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this user's picture",
        )

    old_filename = current_user.image_file
    if old_filename is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User does not have an uploaded picture.",
        )

    current_user.image_file = None
    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)

    delete_profile_image(old_filename)
    return current_user
