from app.db import (
    begin_engine_and_create_tables,
    get_async_session,
    dispose_async_engine,
)
from app.models import User
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from passlib.hash import pbkdf2_sha256
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select


@asynccontextmanager
async def lifespan(app: FastAPI):
    await begin_engine_and_create_tables()
    yield
    await dispose_async_engine()


app = FastAPI(lifespan=lifespan)


def hash_password(password) -> str:
    return pbkdf2_sha256.hash(password)


def verify_password(password, hash) -> bool:
    return pbkdf2_sha256.verify(password, hash)


@app.get("/users")
async def list_users(session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(select(User))
    users = [row[0] for row in result.all()]
    return users


@app.get("/create_users")
async def create_users(session: AsyncSession = Depends(get_async_session)):
    user1 = User(username="user1", hashed_password=hash_password("user1pw"))
    user2 = User(username="user2", hashed_password=hash_password("user2pw"))
    user3 = User(username="user3", hashed_password=hash_password("user3pw"))

    session.add(user1)
    session.add(user2)
    session.add(user3)

    await session.commit()
    return [user1, user2, user3]
