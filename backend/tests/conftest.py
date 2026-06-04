"""Shared test fixtures — in-memory SQLite database + FastAPI TestClient."""

import os

# Override DATABASE_URL before any app imports
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-key"

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.adapters.persistence.database import Base, get_async_session
from src.main import create_app

# In-memory SQLite engine for tests
test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
test_session_factory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_session():
    async with test_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@pytest.fixture(autouse=True)
async def setup_db():
    """Create all tables before each test, drop after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client():
    """Async HTTP client pointed at the FastAPI app with test DB."""
    app = create_app()
    app.dependency_overrides[get_async_session] = override_get_session

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as c:
        yield c


@pytest.fixture
async def auth_client(client: AsyncClient):
    """Client that is already registered, logged in, and has a club."""
    # Register
    await client.post("/v1/auth/register", json={"email": "test@test.pl", "password": "test123"})

    # Login
    login = await client.post("/v1/auth/login", json={"email": "test@test.pl", "password": "test123"})
    tokens = login.json()
    token = tokens["access_token"]

    # Create club
    club = await client.post(
        "/v1/clubs",
        json={"name": "Test Club"},
        headers={"Authorization": f"Bearer {token}"},
    )
    club_id = club.json()["id"]

    # Re-login to get token with club context
    login2 = await client.post("/v1/auth/login", json={"email": "test@test.pl", "password": "test123"})
    token = login2.json()["access_token"]

    # Attach auth header and club_id to client
    client.headers["Authorization"] = f"Bearer {token}"
    client._club_id = club_id  # type: ignore
    return client
