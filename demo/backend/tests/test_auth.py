"""Tests for authentication endpoints."""

import pytest
import pytest_asyncio
from httpx import AsyncClient


class TestAuthEndpoints:
    """Authentication endpoint tests."""

    @pytest.mark.asyncio
    async def test_health_check(self, client: AsyncClient):
        """Health endpoint should return 200 without auth."""
        resp = await client.get("/api/v1/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["service"] == "CSCV2025 Secure Platform"

    @pytest.mark.asyncio
    async def test_register_new_user(self, client: AsyncClient):
        """Register a new user."""
        resp = await client.post(
            "/api/v1/auth/register",
            json={
                "username": "newuser",
                "email": "new@example.com",
                "password": "StrongPass1",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["username"] == "newuser"
        assert data["email"] == "new@example.com"
        assert data["role"] == "viewer"

    @pytest.mark.asyncio
    async def test_register_duplicate_username(self, client: AsyncClient):
        """Cannot register with existing username."""
        await client.post(
            "/api/v1/auth/register",
            json={"username": "dup", "email": "a@b.com", "password": "StrongPass1"},
        )
        resp = await client.post(
            "/api/v1/auth/register",
            json={"username": "dup", "email": "c@d.com", "password": "StrongPass1"},
        )
        assert resp.status_code == 409

    @pytest.mark.asyncio
    async def test_register_weak_password(self, client: AsyncClient):
        """Reject weak password (no uppercase)."""
        resp = await client.post(
            "/api/v1/auth/register",
            json={"username": "weak", "email": "w@b.com", "password": "weakpass1"},
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient):
        """Login with valid credentials."""
        await client.post(
            "/api/v1/auth/register",
            json={"username": "logintest", "email": "login@test.com", "password": "LoginTest1"},
        )
        resp = await client.post(
            "/api/v1/auth/login",
            json={"username": "logintest", "password": "LoginTest1"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == 3600

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, client: AsyncClient):
        """Login with wrong password returns 401."""
        await client.post(
            "/api/v1/auth/register",
            json={"username": "failtest", "email": "fail@test.com", "password": "FailTest1"},
        )
        resp = await client.post(
            "/api/v1/auth/login",
            json={"username": "failtest", "password": "wrongpassword"},
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Login with nonexistent user returns 401."""
        resp = await client.post(
            "/api/v1/auth/login",
            json={"username": "nonexistent", "password": "password"},
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_refresh_token(self, client: AsyncClient):
        """Refresh access token using refresh token."""
        await client.post(
            "/api/v1/auth/register",
            json={"username": "refreshtest", "email": "refresh@test.com", "password": "Refresh123!"},
        )
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={"username": "refreshtest", "password": "Refresh123!"},
        )
        refresh_token = login_resp.json()["refresh_token"]

        resp = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data

    @pytest.mark.asyncio
    async def test_get_me_requires_auth(self, client: AsyncClient):
        """GET /me without token returns 403."""
        resp = await client.get("/api/v1/auth/me")
        assert resp.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_get_me_success(self, client: AsyncClient):
        """GET /me with valid token returns user."""
        await client.post(
            "/api/v1/auth/register",
            json={"username": "metest", "email": "me@test.com", "password": "MeTest123!"},
        )
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={"username": "metest", "password": "MeTest123!"},
        )
        token = login_resp.json()["access_token"]

        resp = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["username"] == "metest"
