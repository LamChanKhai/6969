"""Tests for monitoring and pipeline endpoints."""

import pytest
from httpx import AsyncClient


class TestMonitoringEndpoints:
    """Monitoring dashboard endpoint tests."""

    @pytest.mark.asyncio
    async def test_system_health(self, client: AsyncClient, operator_token: str):
        """System health returns valid data."""
        resp = await client.get(
            "/api/v1/monitoring/health",
            headers={"Authorization": f"Bearer {operator_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert data["uptime_seconds"] >= 0

    @pytest.mark.asyncio
    async def test_system_metrics(self, client: AsyncClient, operator_token: str):
        """System metrics returns valid data."""
        resp = await client.get(
            "/api/v1/monitoring/metrics",
            headers={"Authorization": f"Bearer {operator_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "cpu_usage_percent" in data
        assert "memory_usage_percent" in data
        assert "disk_usage_percent" in data

    @pytest.mark.asyncio
    async def test_security_dashboard(self, client: AsyncClient, operator_token: str):
        """Security dashboard returns valid data."""
        resp = await client.get(
            "/api/v1/monitoring/security-dashboard",
            headers={"Authorization": f"Bearer {operator_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "total_events" in data
        assert "events_by_severity" in data
        assert "blocked_uploads" in data
        assert "active_threats" in data
        assert "top_vulnerabilities" in data

    @pytest.mark.asyncio
    async def test_monitoring_requires_auth(self, client: AsyncClient):
        """Monitoring endpoints require authentication."""
        resp = await client.get("/api/v1/monitoring/health")
        assert resp.status_code in (401, 403)


class TestPipelineEndpoints:
    """DevSecOps pipeline endpoint tests."""

    @pytest.mark.asyncio
    async def test_pipeline_overview(self, client: AsyncClient, operator_token: str):
        """Pipeline overview returns valid data."""
        resp = await client.get(
            "/api/v1/pipeline/overview",
            headers={"Authorization": f"Bearer {operator_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "stages" in data
        assert "latest_runs" in data
        assert "overall_status" in data

    @pytest.mark.asyncio
    async def test_pipeline_requires_auth(self, client: AsyncClient):
        """Pipeline endpoints require authentication."""
        resp = await client.get("/api/v1/pipeline/overview")
        assert resp.status_code in (401, 403)
