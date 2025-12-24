from app.auth import (
    ACCESS_TOKEN_EXPIRE_DAYS,
    create_access_token,
    get_current_user,
    hash_password,
    Token,
    verify_password,
)
from app.db import (
    get_async_session,
    dispose_async_engine,
)
from app.models import DiscussionThread, User
from .routers import discussion_threads

from contextlib import asynccontextmanager
from datetime import timedelta
from fastapi import Depends, FastAPI, Form, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from typing import Annotated


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await dispose_async_engine()


app = FastAPI(lifespan=lifespan)
app.include_router(discussion_threads.router)


@app.post("/token/")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: AsyncSession = Depends(get_async_session),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
        headers={"WWW-Authenticate": "Bearer"},
    )
    statement = select(User).where(User.username == form_data.username)
    results = await session.execute(statement)
    user = results.scalar()
    if user is None:
        raise credentials_exception

    is_password_verified = verify_password(form_data.password, user.hashed_password)
    if not is_password_verified:
        raise credentials_exception

    access_token_expires = timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")


@app.post("/user/create/")
async def create_user(
    username: Annotated[str, Form()],
    password: Annotated[str, Form()],
    confirm_password: Annotated[str, Form()],
    session: AsyncSession = Depends(get_async_session),
):
    if password != confirm_password:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Two passwords are not the same",
        )
    try:
        new_user = User(username=username, hashed_password=hash_password(password))
        session.add(new_user)
        await session.commit()
        return {"message": "New user created"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(e)
        )


@app.get("/user/discussion_threads/")
async def my_discussion_threads(
    current_user: Annotated[User, Depends(get_current_user)],
    session: AsyncSession = Depends(get_async_session),
):
    statement = select(DiscussionThread).where(
        DiscussionThread.user_id == current_user.id
    )
    results = await session.execute(statement)
    discussion_threads = results.scalars().all()
    return discussion_threads
