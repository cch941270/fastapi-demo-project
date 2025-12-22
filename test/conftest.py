from app import models
from app.db import get_async_session
from main import app

import asyncpg
from dotenv import dotenv_values
from httpx import ASGITransport, AsyncClient
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

config = dotenv_values(".env")
TEST_DATABASE_URL = "postgresql+asyncpg://{}:{}@{}:{}/{}".format(
    config.get("DB_USER"),
    config.get("DB_PASSWORD"),
    config.get("DB_HOST"),
    config.get("DB_PORT"),
    config.get("TEST_DB_NAME"),
)
async_engine = create_async_engine(TEST_DATABASE_URL, echo=False, poolclass=NullPool)
async_session = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_database():
    conn = await asyncpg.connect(
        user=config.get("DB_USER"),
        password=config.get("DB_PASSWORD"),
        host=config.get("DB_HOST"),
        port=config.get("DB_PORT"),
        database=config.get("DB_NAME"),
    )
    await conn.execute(f'DROP DATABASE IF EXISTS "{config.get("TEST_DB_NAME")}" WITH (FORCE)')
    await conn.execute(f'CREATE DATABASE "{config.get("TEST_DB_NAME")}"')
    yield
    await conn.execute(f'DROP DATABASE IF EXISTS "{config.get("TEST_DB_NAME")}" WITH (FORCE)')
    await conn.close()

@pytest_asyncio.fixture(scope="function")
async def get_async_engine():
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield async_engine
    await async_engine.dispose(close=False)

@pytest_asyncio.fixture(scope="function")
async def get_test_async_session(get_async_engine):
    async with async_session() as session:
        await session.begin()
        yield session
        await session.rollback()

@pytest_asyncio.fixture(scope="function", autouse=True)
async def async_client(get_test_async_session):
    def override_get_async_session():
        yield get_test_async_session
    app.dependency_overrides[get_async_session] = override_get_async_session
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost")
