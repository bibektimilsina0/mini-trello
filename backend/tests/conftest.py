import os
from pathlib import Path
from typing import AsyncGenerator
import re
import pytest_asyncio
from dotenv import load_dotenv
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

env_test_path = Path(__file__).parent.parent / ".env.test"
loaded = load_dotenv(env_test_path)

if not loaded:
    raise RuntimeError(f"Could not find .env.test at {env_test_path} — create it before running tests.")

if "TEST_DATABASE_URL" not in os.environ:
    raise RuntimeError("TEST_DATABASE_URL not set — check .env.test contains it.")

os.environ["DATABASE_URL"] = os.environ["TEST_DATABASE_URL"]
print(f"[conftest] Using test database: {os.environ['DATABASE_URL'][:40]}...")

from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import user, token, workspace, board  # noqa: E402, F401
from app.models import list as list_model, card, comment  # noqa: E402, F401

TEST_DATABASE_URL = os.environ["DATABASE_URL"]

# NullPool: never reuse a connection across checkouts. Required here because
# each test may run under a fresh event loop (see pytest.ini's
# asyncio_default_fixture_loop_scope) — reusing a pooled asyncpg connection
# from a previous, now-closed loop is exactly what caused "another operation
# is in progress" / "Event loop is closed".
engine = create_async_engine(TEST_DATABASE_URL, connect_args={"ssl": "require"}, poolclass=NullPool)
TestSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        yield session

@pytest_asyncio.fixture
async def verified_client(client: AsyncClient, capsys) -> AsyncClient:
    """A client that's already signed up, verified, and logged in.
    Returns the same AsyncClient with session cookies already set."""
    await client.post(
        "/api/auth/signup",
        json={"email": "test@example.com", "name": "Test User", "password": "password123"},
    )
    captured = capsys.readouterr()
    token = re.search(r"token=([a-f0-9]+)", captured.out).group(1)
    await client.get("/api/auth/verify-email", params={"token": token})
    await client.post("/api/auth/login", json={"email": "test@example.com", "password": "password123"})
    return client