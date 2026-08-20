from datetime import UTC, datetime, timedelta
from idlelib import query

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pwdlib import PasswordHash
import pwdlib
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.models import User
from src.database import get_db
from typing import TypedDict, cast


from src.config import settings

password_hasher = PasswordHash.recommended()

DUMMY_HASH = "$argon2id$v=19$m=65536,t=3,p=4$Ke04ppvRwTWi1kkItmHb9g$r7yis/cN3wg/UpebnSI3kY98UQuEu+7EMvCTyRzygX4"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")


class TokenPayload(TypedDict):
    sub: str
    is_admin: bool


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hasher.verify(plain_password, hashed_password)


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | None:

    user = (await db.execute(select(User).where(User.email == email))).scalars().first()

    if not user:
        verify_password(password, DUMMY_HASH)
        return None

    if not verify_password(password, user.password):
        return None

    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:

    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(
            minutes=settings.access_token_ex,
        )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY.get_secret_value(),
        algorithm=settings.algorithm,
    )
    return encoded_jwt


def verify_access_token(token: str) -> TokenPayload | None:

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY.get_secret_value(),
            algorithms=[settings.algorithm],
            options={"require": ["exp", "sub", "is_admin"]},
        )
    except jwt.InvalidTokenError:
        return None
    else:
        return cast(
            TokenPayload, {"sub": payload["sub"], "is_admin": payload["is_admin"]}
        )


async def get_token_payload(token: str = Depends(oauth2_scheme)) -> TokenPayload:
    token_data = verify_access_token(token)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token_data


async def get_current_user(
    token_data: TokenPayload = Depends(get_token_payload),
) -> int:

    return int(token_data["sub"])


async def get_admin_user(
    token_data: TokenPayload = Depends(get_token_payload)
) -> int:

    if not token_data["is_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not an administrator",
        )

    return int(token_data["sub"])
