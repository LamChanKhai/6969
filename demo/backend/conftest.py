"""Pytest configuration."""

import asyncio
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.core.database import Base, get_db
from app.main import app

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False, future=True)
TestSession = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_db():
    """Create tables before each test and drop them after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a test database session."""
    async with TestSession() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Provide an async HTTP test client with DB override."""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def admin_token(client: AsyncClient) -> str:
    """Create admin user and return access token."""
    await client.post(
        "/api/v1/auth/register",
        json={"username": "testadmin", "email": "admin@test.com", "password": "Admin123!"},
    )
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "testadmin", "password": "Admin123!"},
    )
    return response.json()["access_token"]


@pytest_asyncio.fixture(scope="function")
async def operator_token(client: AsyncClient) -> str:
    """Create operator user and return access token."""
    await client.post(
        "/api/v1/auth/register",
        json={"username": "testop", "email": "op@test.com", "password": "Operator123!"},
    )
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "testop", "password": "Operator123!"},
    )
    return response.json()["access_token"]
