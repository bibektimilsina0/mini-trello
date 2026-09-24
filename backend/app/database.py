from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

# Neon (or any Postgres) async URL must use the asyncpg driver:
# postgresql+asyncpg://user:pass@host/dbname
engine = create_async_engine(settings.database_url, echo=False, pool_pre_ping=True, connect_args={"ssl": "require"})
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
