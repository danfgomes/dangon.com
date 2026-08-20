from logging import raiseExceptions
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Request

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select


from src.auth import (
    create_access_token,
    hash_password,
    oauth2_scheme,
    verify_password,
    verify_access_token,
    get_current_user,
    authenticate_user,
)


from src.models.user import User
from src.database import get_db


from src.schemas.auth import Token
from src.schemas.user import UserCreate, UserPublic, UserUpdate

from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter(
    prefix="/users",
    tags=["users"],
)


@router.post("/create", response_model=UserPublic)
async def create_user(user_in: UserCreate, db: AsyncSession = Depends(get_db)):

    query = select(User).where(
        (User.email == user_in.email) | (User.username == user_in.username)
    )

    result = await db.execute(query)
    existing_user = result.scalars().first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email or username already registered",
        )

    hashed_password = hash_password(user_in.password)
    db_user = User(**user_in.model_dump(exclude={"password"}), password=hashed_password)

    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)

    return db_user


@router.patch("/{user_id}", response_model=UserPublic)
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


@router.post("/login", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: AsyncSession = Depends(get_db),
):
    user = await authenticate_user(db, form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="The data is incorrect!",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}


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
