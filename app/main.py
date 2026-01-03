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
from dotenv import dotenv_values
from fastapi import Depends, FastAPI, Form, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col, select
import time
from typing import Annotated


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await dispose_async_engine()


app = FastAPI(lifespan=lifespan)
app.include_router(discussion_threads.router)

origins = ["http://localhost:5173"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

config = dotenv_values(".env")
image_path = config.get("IMAGE_PATH") or "/static"
app.mount(image_path, StaticFiles(directory="static/images"), name="discussion_thread_images")

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    end_time = time.perf_counter()
    process_time = f"{(end_time - start_time) * 1000}ms"
    response.headers["X-Process-Time"] = process_time
    return response

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
    statement = select(DiscussionThread, User) \
        .where(DiscussionThread.user_id == User.id) \
        .where(DiscussionThread.user_id == current_user.id) \
        .order_by(col(DiscussionThread.created_at).desc())
    results = await session.execute(statement)
    return discussion_threads.format_discussion_threads(results)
