"""Tests for user management endpoints."""

import pytest
from httpx import AsyncClient


class TestUserEndpoints:
    """User management endpoint tests."""

    @pytest.mark.asyncio
    async def test_list_users_admin(self, client: AsyncClient, admin_token: str):
        """Admin can list users."""
        resp = await client.get(
            "/api/v1/users/",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_list_users_forbidden_viewer(self, client: AsyncClient, operator_token: str):
        """Non-admin cannot list users."""
        resp = await client.get(
            "/api/v1/users/",
            headers={"Authorization": f"Bearer {operator_token}"},
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_get_own_profile(self, client: AsyncClient, operator_token: str):
        """User can get own profile."""
        # First get own user ID
        me_resp = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {operator_token}"},
        )
        user_id = me_resp.json()["id"]

        resp = await client.get(
            f"/api/v1/users/{user_id}",
            headers={"Authorization": f"Bearer {operator_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == user_id

    @pytest.mark.asyncio
    async def test_get_user_not_found(self, client: AsyncClient, operator_token: str):
        """Get nonexistent user returns 404."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        resp = await client.get(
            f"/api/v1/users/{fake_id}",
            headers={"Authorization": f"Bearer {operator_token}"},
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_change_password(self, client: AsyncClient, operator_token: str):
        """User can change own password."""
        me_resp = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {operator_token}"},
        )
        user_id = me_resp.json()["id"]

        resp = await client.post(
            f"/api/v1/users/{user_id}/change-password",
            params={"new_password": "NewPassword1!"},
            headers={"Authorization": f"Bearer {operator_token}"},
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_change_password_too_short(self, client: AsyncClient, operator_token: str):
        """Reject password shorter than 8 characters."""
        me_resp = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {operator_token}"},
        )
        user_id = me_resp.json()["id"]

        resp = await client.post(
            f"/api/v1/users/{user_id}/change-password",
            params={"new_password": "Short1!"},
            headers={"Authorization": f"Bearer {operator_token}"},
        )
        assert resp.status_code == 400
