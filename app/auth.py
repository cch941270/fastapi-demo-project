from app.db import get_async_session
from app.models import User
from datetime import datetime, timedelta, UTC
from dotenv import dotenv_values
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from jwt.exceptions import InvalidTokenError
from passlib.hash import pbkdf2_sha256
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from typing import Annotated

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
config = dotenv_values(".env")
SECRET_KEY = config.get("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 1.0

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None

def hash_password(password) -> str:
    return pbkdf2_sha256.hash(password)

def verify_password(password, hash) -> bool:
    return pbkdf2_sha256.verify(password, hash)

def create_access_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.now(UTC) + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: AsyncSession = Depends(get_async_session)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exception
    statement = select(User).where(User.username == token_data.username)
    results = await session.execute(statement)
    user = results.scalar()
    if user is None:
        raise credentials_exception
    return user
