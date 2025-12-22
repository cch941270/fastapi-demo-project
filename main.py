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


async def get_discussion_thread(
    discussion_thread_id: int, session: AsyncSession = Depends(get_async_session)
):
    statement = select(DiscussionThread).where(
        DiscussionThread.id == discussion_thread_id
    )
    results = await session.execute(statement)
    discussion_thread = results.scalar()
    if discussion_thread is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Discussion thread not found"
        )
    return discussion_thread


@app.get("/discussion_threads/")
async def list_discussion_threads(
    search_title: str | None = None, session: AsyncSession = Depends(get_async_session)
):
    if search_title is None:
        statement = select(DiscussionThread)
    else:
        statement = select(DiscussionThread).where(
            col(DiscussionThread.title).contains(search_title)
        )
    results = await session.execute(statement)
    discussion_threads = results.scalars().all()
    return discussion_threads


@app.post("/discussion_threads/create/")
async def create_discussion_thread(
    title: Annotated[str, Form()],
    content: Annotated[str, Form()],
    current_user: Annotated[User, Depends(get_current_user)],
    session: AsyncSession = Depends(get_async_session),
):
    try:
        new_discussion_thread = DiscussionThread(
            user_id=current_user.id, title=title, content=content
        )
        session.add(new_discussion_thread)
        await session.commit()
        return {"message": "New discussion thread created"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(e)
        )


@app.get("/discussion_threads/{discussion_thread_id}/")
async def read_discussion_thread(
    discussion_thread_id: int, session: AsyncSession = Depends(get_async_session)
):
    discussion_thread = await get_discussion_thread(discussion_thread_id, session)
    return discussion_thread


@app.patch("/discussion_threads/{discussion_thread_id}/")
async def update_discussion_thread(
    discussion_thread_id: int,
    content: Annotated[str, Form()],
    current_user: Annotated[User, Depends(get_current_user)],
    session: AsyncSession = Depends(get_async_session),
):
    discussion_thread = await get_discussion_thread(discussion_thread_id, session)
    if discussion_thread.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="This is not your discussion thread",
        )
    try:
        discussion_thread.content = content
        discussion_thread.updated_at = datetime.now(UTC)
        session.add(discussion_thread)
        await session.commit()
        return discussion_thread
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(e)
        )


@app.delete("/discussion_threads/{discussion_thread_id}/")
async def delete_discussion_thread(
    discussion_thread_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: AsyncSession = Depends(get_async_session),
):
    discussion_thread = await get_discussion_thread(discussion_thread_id, session)
    if discussion_thread.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="This is not your discussion thread",
        )
    try:
        await session.delete(discussion_thread)
        await session.commit()
        return {"message": "Discussion thread deleted"}
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
