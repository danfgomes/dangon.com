from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from auth import (
    create_access_token,
    hash_password,
    oauth2_scheme,
    verify_password,
    verify_access_token,
)

from config import settings
import models
from database import get_db

# 1. UserUpdate importado aqui
from schemas import PostResponse, UserCreate, UserPublic, UserPrivate, Token, UserUpdate

from datetime import timedelta
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter(
    prefix="/users",
    tags=["users"],
)

@router.post("/create", response_model=UserPublic)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):

    query = select(models.User).where(
        (models.User.email == user.email) | (models.User.username == user.username)
    )
    result = await db.execute(query)
    existing_user = result.scalars().first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email or username already registered"
        )

    hashed_password = hash_password(user.password)
    db_user = models.User(username=user.username, email=user.email, password=hashed_password)

    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)

    return db_user


@router.patch("/{user_id}", response_model=UserPublic)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: AsyncSession = Depends(get_db)
):

    query = select(models.User).where(models.User.id == user_id)
    result = await db.execute(query)
    db_user = result.scalars().first()

    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    update_data = user_update.model_dump(exclude_unset=True)


    if "password" in update_data:
        update_data["password"] = hash_password(update_data["password"])

    for key, value in update_data.items():
        setattr(db_user, key, value)


    await db.commit()
    await db.refresh(db_user)

    return db_user


@router.get("/{user_id}", response_model=UserPublic)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)): # 4. Sintaxe da função corrigida


    query = select(models.User).where(models.User.id == user_id)


    result = await db.execute(query)
    existing_user = result.scalars().first()

    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found!"
        )

    return existing_user

@router.post("/login", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: AsyncSession = Depends(get_db)
):


    query = select(models.User).where(
        (models.User.email == form_data.username) | (models.User.username == form_data.username)
    )
    result = await db.execute(query)
    user = result.scalars().first()

    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="The data is incorrect!",
            headers={"WWW-Authenticate": "Bearer"}
        )

    access_token = create_access_token(
        data={"sub": str(user.id)}
    )


    return {"access_token": access_token, "token_type": "bearer"}

@router.delete("/{user_id}", status_code = status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id : int,
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):

    token_data = verify_access_token(token)

    query = select(models.User).where(models.User.id == user_id)
    result = await db.execute(query)
    db_user = result.scalars().first()

    if not db_user:
        raise HTTPException (
            status_code=status.HTTP_404_NOT_FOUND,
            detail= "User not found"
        )

    if str(db_user.id) != token_data:
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN,
            detail= "Voce não tem permissão para deletar o outro usuário!"
        )

    await db.delete(db_user)
    await db.commit()

