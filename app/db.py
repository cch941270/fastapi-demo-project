from dotenv import dotenv_values
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

config = dotenv_values(".env")
DATABASE_URL = "postgresql+asyncpg://{}:{}@{}:{}/{}".format(
    config.get("DB_USER"),
    config.get("DB_PASSWORD"),
    config.get("DB_HOST"),
    config.get("DB_PORT"),
    config.get("DB_NAME"),
)

async_engine = create_async_engine(DATABASE_URL, echo=True, pool_pre_ping=True)
async_session = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)


async def dispose_async_engine():
    await async_engine.dispose()


async def get_async_session():
    async with async_session() as session:
        yield session
