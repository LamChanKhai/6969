"""Tests for file upload endpoints."""

import io
import zipfile
import pytest
from httpx import AsyncClient, UploadFile


class TestUploadEndpoints:
    """File upload endpoint tests."""

    @pytest.mark.asyncio
    async def test_upload_requires_auth(self, client: AsyncClient):
        """Upload without auth returns 403."""
        resp = await client.post("/api/v1/uploads/")
        assert resp.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_upload_text_file(self, client: AsyncClient, operator_token: str):
        """Upload a plain text file."""
        content = b"Hello, this is a test file for CSCV2025 demo."
        resp = await client.post(
            "/api/v1/uploads/",
            files={"file": ("test.txt", content, "text/plain")},
            headers={"Authorization": f"Bearer {operator_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["original_filename"] == "test.txt"
        assert data["security_scan_status"] == "passed"
        assert data["extraction_status"] == "not_applicable"

    @pytest.mark.asyncio
    async def test_upload_safe_zip(self, client: AsyncClient, operator_token: str):
        """Upload a safe ZIP archive."""
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("document.txt", "Safe content inside the archive.")
            zf.writestr("readme.txt", "Another safe file.")
        zip_buffer.seek(0)

        resp = await client.post(
            "/api/v1/uploads/",
            files={"file": ("safe_archive.zip", zip_buffer.read(), "application/zip")},
            headers={"Authorization": f"Bearer {operator_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["security_scan_status"] == "passed"
        assert data["extraction_status"] == "completed"
        assert data["extracted"] is True

    @pytest.mark.asyncio
    async def test_upload_blocked_extension(self, client: AsyncClient, operator_token: str):
        """Upload of .exe file is blocked."""
        resp = await client.post(
            "/api/v1/uploads/",
            files={"file": ("malware.exe", b"fake exe content", "application/octet-stream")},
            headers={"Authorization": f"Bearer {operator_token}"},
        )
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_upload_path_traversal_zip(self, client: AsyncClient, operator_token: str):
        """ZIP with path traversal is blocked."""
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("../../etc/passwd", "hacked")
        zip_buffer.seek(0)

        resp = await client.post(
            "/api/v1/uploads/",
            files={"file": ("traversal.zip", zip_buffer.read(), "application/zip")},
            headers={"Authorization": f"Bearer {operator_token}"},
        )
        # Should be accepted but marked as blocked after scan
        if resp.status_code == 200:
            data = resp.json()
            assert data["security_scan_status"] == "blocked"

    @pytest.mark.asyncio
    async def test_list_uploads(self, client: AsyncClient, operator_token: str):
        """List uploaded files."""
        # Upload a file first
        await client.post(
            "/api/v1/uploads/",
            files={"file": ("list_test.txt", b"test content", "text/plain")},
            headers={"Authorization": f"Bearer {operator_token}"},
        )

        resp = await client.get(
            "/api/v1/uploads/",
            headers={"Authorization": f"Bearer {operator_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert data["total"] >= 1

    @pytest.mark.asyncio
    async def test_get_upload_by_id(self, client: AsyncClient, operator_token: str):
        """Get specific upload by ID."""
        # Upload first
        upload_resp = await client.post(
            "/api/v1/uploads/",
            files={"file": ("get_test.txt", b"get test", "text/plain")},
            headers={"Authorization": f"Bearer {operator_token}"},
        )
        upload_id = upload_resp.json()["id"]

        resp = await client.get(
            f"/api/v1/uploads/{upload_id}",
            headers={"Authorization": f"Bearer {operator_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == upload_id

    @pytest.mark.asyncio
    async def test_get_extraction_status(self, client: AsyncClient, operator_token: str):
        """Get extraction status for a ZIP upload."""
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("file1.txt", "content 1")
        zip_buffer.seek(0)

        upload_resp = await client.post(
            "/api/v1/uploads/",
            files={"file": ("extract_test.zip", zip_buffer.read(), "application/zip")},
            headers={"Authorization": f"Bearer {operator_token}"},
        )
        upload_id = upload_resp.json()["id"]

        resp = await client.get(
            f"/api/v1/uploads/{upload_id}/extraction-status",
            headers={"Authorization": f"Bearer {operator_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["upload_id"] == upload_id
        assert data["status"] == "completed"
        assert len(data["events"]) >= 2

    @pytest.mark.asyncio
    async def test_upload_empty_file(self, client: AsyncClient, operator_token: str):
        """Reject empty file upload."""
        resp = await client.post(
            "/api/v1/uploads/",
            files={"file": ("empty.txt", b"", "text/plain")},
            headers={"Authorization": f"Bearer {operator_token}"},
        )
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_viewers_cannot_upload(self, client: AsyncClient):
        """Viewer role cannot upload files."""
        # Register as viewer
        await client.post(
            "/api/v1/auth/register",
            json={"username": "viewertest", "email": "viewer@test.com", "password": "ViewerTest1"},
        )
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={"username": "viewertest", "password": "ViewerTest1"},
        )
        token = login_resp.json()["access_token"]

        resp = await client.post(
            "/api/v1/uploads/",
            files={"file": ("test.txt", b"content", "text/plain")},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403
