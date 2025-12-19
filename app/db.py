from dotenv import dotenv_values
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlmodel import SQLModel
from typing import AsyncGenerator

config = dotenv_values(".env")
DATABASE_URL = f"postgresql+asyncpg://{config.get("DB_USER_PASSWORD")}@{config.get("DB_HOST_PORT")}/{config.get("DB_NAME")}"
async_engine = create_async_engine(DATABASE_URL, echo=True)
async_session = async_sessionmaker(async_engine, expire_on_commit=False)


async def begin_engine_and_create_tables():
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def dispose_async_engine():
    await async_engine.dispose()


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session
