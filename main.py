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
from app.models import Thread, User

from contextlib import asynccontextmanager
from datetime import datetime, timedelta, UTC
from fastapi import Depends, FastAPI, Form, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, col
from typing import Annotated


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await dispose_async_engine()


app = FastAPI(lifespan=lifespan)


async def get_thread(
    thread_id: int, session: AsyncSession = Depends(get_async_session)
):
    statement = select(Thread).where(Thread.id == thread_id)
    results = await session.execute(statement)
    thread = results.scalar()
    if thread is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Thread not found"
        )
    return thread


@app.get("/threads/")
async def list_threads(
    search_title: str | None = None, session: AsyncSession = Depends(get_async_session)
):
    if search_title is None:
        statement = select(Thread)
    else:
        statement = select(Thread).where(col(Thread.title).contains(search_title))
    results = await session.execute(statement)
    threads = results.scalars().all()
    return threads


@app.post("/threads/create/")
async def create_thread(
    title: Annotated[str, Form()],
    content: Annotated[str, Form()],
    current_user: Annotated[User, Depends(get_current_user)],
    session: AsyncSession = Depends(get_async_session),
):
    try:
        new_thread = Thread(user_id=current_user.id, title=title, content=content)
        session.add(new_thread)
        await session.commit()
        return {"message": "New thread created"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(e)
        )


@app.get("/threads/{thread_id}/")
async def read_thread(
    thread_id: int, session: AsyncSession = Depends(get_async_session)
):
    thread = await get_thread(thread_id, session)
    return thread


@app.patch("/threads/{thread_id}/")
async def update_thread(
    thread_id: int,
    content: Annotated[str, Form()],
    current_user: Annotated[User, Depends(get_current_user)],
    session: AsyncSession = Depends(get_async_session),
):
    thread = await get_thread(thread_id, session)
    if thread.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="This is not your thread."
        )
    try:
        thread.content = content
        thread.updated_at = datetime.now(UTC)
        session.add(thread)
        await session.commit()
        return thread
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(e)
        )


@app.delete("/threads/{thread_id}/")
async def delete_thread(
    thread_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: AsyncSession = Depends(get_async_session),
):
    thread = await get_thread(thread_id, session)
    if thread.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="This is not your thread."
        )
    try:
        await session.delete(thread)
        await session.commit()
        return {"message": "Thread deleted"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(e)
        )


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
            detail="Two passwords are not the same.",
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


@app.get("/user/threads/")
async def my_threads(
    current_user: Annotated[User, Depends(get_current_user)],
    session: AsyncSession = Depends(get_async_session),
):
    statement = select(Thread).where(Thread.user_id == current_user.id)
    results = await session.execute(statement)
    threads = results.scalars().all()
    return threads
