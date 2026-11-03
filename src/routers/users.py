
from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import Annotated
from fastapi.templating import Jinja2Templates

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, func


from src.auth import (
    create_access_token,
    hash_password,
    get_current_user,
    authenticate_user,
)


from src.models.user import User
from src.database import get_db


from src.schemas.auth import Token
from src.schemas.user import UserCreate, UserPublic, UserUpdate, UserPrivate
from fastapi.security import OAuth2PasswordRequestForm



router = APIRouter(
    prefix="/api/users",
    tags=["users"],
)

templates = Jinja2Templates(directory="src/templates")


@router.get("/create-account", include_in_schema=False)
async def create_account_page(request: Request):
    return templates.TemplateResponse(request=request, name="createcont.html")

@router.post("/create",
            response_model=UserPrivate,
            status_code=status.HTTP_201_CREATED
)
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
        password=hashed_password
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
async def get_current_user_in(
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user)
):

    query = select(User).where(User.id == current_user_id)
    result = await db.execute(query)
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    return user

@router.patch("/{user_id}", response_model=UserPrivate)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: AsyncSession = Depends(get_db),
    user_authenticate: int = Depends(get_current_user),
):

    if user_authenticate != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access blocked. The resource belongs to another account.",
        )

    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    db_user = result.scalars().first()

    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    update_data = user_update.model_dump(exclude_unset=True)

    if "password" in update_data:
        update_data["password"] = hash_password(update_data["password"])

    for key, value in update_data.items():
        setattr(db_user, key, value)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Dado inoperante!."
        )

    await db.refresh(db_user)
    return db_user


@router.get("/{user_id}", response_model=UserPublic)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    user_authenticate=Depends(get_current_user),
):

    if user_authenticate != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access blocked. The resource belongs to another account.",
        )

    query = select(User).where(User.id == user_id)

    result = await db.execute(query)
    existing_user = result.scalars().first()

    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found!"
        )

    return existing_user









@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    db: AsyncSession = Depends(get_db), current_user_id: str = Depends(get_current_user)
):

    query = select(User).where(User.id == int(current_user_id))
    result = await db.execute(query)
    db_user = result.scalars().first()

    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    await db.delete(db_user)
    await db.commit()
