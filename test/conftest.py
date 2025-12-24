from app.auth import get_current_user
from app.db import get_async_session
from app.models import DiscussionThread, User
from app.main import app

import asyncpg
from dotenv import dotenv_values
from httpx import ASGITransport, AsyncClient
from passlib.hash import pbkdf2_sha256
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
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False, poolclass=NullPool)
test_session = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

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
async def get_test_engine():
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield test_engine
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)

@pytest_asyncio.fixture(scope="function")
async def get_test_session(get_test_engine):
    async with test_session() as session:
        yield session

@pytest_asyncio.fixture(scope="function", autouse=True)
async def async_client(get_test_session):
    def override_get_async_session():
        yield get_test_session
    app.dependency_overrides[get_async_session] = override_get_async_session
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost")

@pytest_asyncio.fixture(scope="function", autouse=True)
async def get_test_user(get_test_session: AsyncSession):
    test_user = User(username="testuser", hashed_password=pbkdf2_sha256.hash("testuserpw"))
    get_test_session.add(test_user)
    await get_test_session.commit()
    def override_get_current_user():
        return test_user
    app.dependency_overrides[get_current_user] = override_get_current_user
    yield test_user

@pytest_asyncio.fixture(scope="function", autouse=True)
async def another_test_user(get_test_session: AsyncSession):
    another_test_user = User(username="testuser2", hashed_password=pbkdf2_sha256.hash("testuser2pw"))
    get_test_session.add(another_test_user)
    await get_test_session.commit()
    yield another_test_user

@pytest_asyncio.fixture(scope="function", autouse=True)
async def mock_discussion_thread(get_test_session: AsyncSession, get_test_user):
    mock_discussion_thread = DiscussionThread(user_id=get_test_user.id, title="testtitle1", content="testcontent1")
    get_test_session.add(mock_discussion_thread)
    await get_test_session.commit()
    yield mock_discussion_thread

@pytest_asyncio.fixture(scope="function", autouse=True)
async def another_mock_discussion_threads(get_test_session: AsyncSession, another_test_user):
    another_mock_discussion_threads = DiscussionThread(user_id=another_test_user.id, title="testtitle2", content="testcontent2")
    get_test_session.add(another_mock_discussion_threads)
    await get_test_session.commit()
    yield another_mock_discussion_threads
