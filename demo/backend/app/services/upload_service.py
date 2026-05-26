"""File upload service with security scanning and sandboxed extraction."""

import asyncio
import mimetypes
import os
import shutil
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.models import FileUpload, ExtractionEvent, SecurityEvent


ALLOWED_MIME_TYPES = {
    "application/zip",
    "application/x-zip-compressed",
    "text/plain",
    "application/pdf",
    "image/png",
    "image/jpeg",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}

BLOCKED_EXTENSIONS = {
    ".exe", ".bat", ".cmd", ".ps1", ".sh", ".php", ".jsp",
    ".asp", ".aspx", ".dll", ".so", ".dylib", ".com", ".scr",
    ".vbs", ".js", ".wsf", ".msi", ".reg", ".hta",
}


def validate_file_extension(filename: str) -> bool:
    """Check if file extension is allowed."""
    ext = os.path.splitext(filename)[1].lower()
    if ext in BLOCKED_EXTENSIONS:
        return False
    return ext in [e.lower() for e in settings.ALLOWED_EXTENSIONS] or ext == ""


def validate_mime_type(mime_type: str) -> bool:
    """Check if MIME type is allowed."""
    if not mime_type:
        return False
    return mime_type in ALLOWED_MIME_TYPES or mime_type.startswith("text/") or mime_type.startswith("application/")


async def validate_zip_contents(file_path: Path, db: AsyncSession, upload_id: uuid.UUID) -> tuple[bool, str]:
    """Validate ZIP archive contents for security threats."""
    try:
        with zipfile.ZipFile(file_path, "r") as zf:
            for entry in zf.namelist():
                # Check for path traversal
                if ".." in entry or entry.startswith("/") or entry.startswith("\\"):
                    await _log_security_event(
                        db, upload_id, "path_traversal_blocked", "critical",
                        f"Blocked path traversal attempt: {entry}",
                        f"ZIP entry contains path traversal: {entry}"
                    )
                    return False, f"Path traversal detected in entry: {entry}"

                # Check for dangerous extensions
                ext = os.path.splitext(entry)[1].lower()
                if ext in BLOCKED_EXTENSIONS:
                    await _log_security_event(
                        db, upload_id, "blocked_extension", "high",
                        f"Blocked dangerous file type: {ext}",
                        f"ZIP entry has blocked extension: {entry}"
                    )
                    return False, f"Blocked file type in archive: {entry}"

                # Check for symlink
                info = zf.getinfo(entry)
                if (info.external_attr >> 16) & 0xA000 == 0xA000:
                    await _log_security_event(
                        db, upload_id, "symlink_blocked", "high",
                        f"Blocked symbolic link: {entry}",
                        f"ZIP entry is a symbolic link: {entry}"
                    )
                    return False, f"Symbolic link detected: {entry}"

                # Check for zip bomb (too many entries)
                if len(zf.namelist()) > 10000:
                    await _log_security_event(
                        db, upload_id, "zip_bomb_detected", "critical",
                        "Potential zip bomb: too many entries",
                        f"ZIP contains {len(zf.namelist())} entries"
                    )
                    return False, "Potential zip bomb: too many entries"
    except zipfile.BadZipFile:
        await _log_security_event(
            db, upload_id, "invalid_archive", "medium",
            "Uploaded file is not a valid ZIP archive",
            "BadZipFile exception during validation"
        )
        return False, "Invalid ZIP archive"

    return True, "Archive validated successfully"


async def extract_archive_sandboxed(
    file_path: Path,
    storage_dir: Path,
    db: AsyncSession,
    upload_id: uuid.UUID,
) -> tuple[bool, str]:
    """Extract archive in a sandboxed directory."""
    try:
        sandbox_dir = storage_dir / "sandbox"
        sandbox_dir.mkdir(parents=True, exist_ok=True)

        await _log_extraction_event(
            db, upload_id, "extraction_started", "Extracting archive in sandbox",
            str(sandbox_dir), "success"
        )

        with zipfile.ZipFile(file_path, "r") as zf:
            extracted_files = []
            for entry_info in zf.infolist():
                target_path = sandbox_dir / entry_info.filename
                # Prevent directory traversal
                if not str(target_path.resolve()).startswith(str(sandbox_dir.resolve())):
                    continue

                if entry_info.is_dir():
                    target_path.mkdir(parents=True, exist_ok=True)
                else:
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    with zf.open(entry_info) as src, open(target_path, "wb") as dst:
                        shutil.copyfileobj(src, dst)
                    extracted_files.append(entry_info.filename)

        await _log_extraction_event(
            db, upload_id, "extraction_completed",
            f"Extracted {len(extracted_files)} files",
            str(sandbox_dir), "success"
        )

        return True, f"Extracted {len(extracted_files)} files"

    except Exception as e:
        await _log_extraction_event(
            db, upload_id, "extraction_failed", str(e),
            str(sandbox_dir), "error"
        )
        return False, str(e)


async def create_upload_record(
    db: AsyncSession,
    user_id: uuid.UUID,
    original_filename: str,
    stored_filename: str,
    file_size: int,
    mime_type: str,
    storage_path: str,
) -> FileUpload:
    """Create a file upload record in the database."""
    upload = FileUpload(
        user_id=user_id,
        original_filename=original_filename,
        stored_filename=stored_filename,
        file_size=file_size,
        mime_type=mime_type,
        storage_path=storage_path,
        extraction_status="pending",
        security_scan_status="pending",
    )
    db.add(upload)
    await db.commit()
    await db.refresh(upload)
    return upload


async def list_uploads(
    db: AsyncSession,
    user_id: Optional[uuid.UUID] = None,
    skip: int = 0,
    limit: int = 20,
) -> tuple[List[FileUpload], int]:
    """List file uploads with optional user filter."""
    query = select(FileUpload)
    count_query = select(func.count(FileUpload.id))

    if user_id is not None:
        query = query.where(FileUpload.user_id == user_id)
        count_query = count_query.where(FileUpload.user_id == user_id)

    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    query = query.order_by(FileUpload.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    uploads = result.scalars().all()
    return uploads, total


async def get_upload_with_events(
    db: AsyncSession,
    upload_id: uuid.UUID,
) -> Optional[FileUpload]:
    """Get upload with related events."""
    result = await db.execute(
        select(FileUpload)
        .options(
            selectinload(FileUpload.extraction_events),
            selectinload(FileUpload.security_events),
        )
        .where(FileUpload.id == upload_id)
    )
    return result.scalar_one_or_none()


async def count_uploads(db: AsyncSession) -> int:
    """Count total uploads."""
    result = await db.execute(select(func.count(FileUpload.id)))
    return result.scalar_one()


async def count_blocked_uploads(db: AsyncSession) -> int:
    """Count blocked uploads."""
    result = await db.execute(
        select(func.count(FileUpload.id)).where(
            FileUpload.security_scan_result.contains("blocked")
        )
    )
    return result.scalar_one()


async def _log_extraction_event(
    db: AsyncSession,
    upload_id: uuid.UUID,
    event_type: str,
    message: str,
    file_path: str,
    status: str,
):
    """Log an extraction event."""
    event = ExtractionEvent(
        upload_id=upload_id,
        event_type=event_type,
        message=message,
        file_path=file_path,
        status=status,
    )
    db.add(event)
    await db.commit()


async def _log_security_event(
    db: AsyncSession,
    upload_id: uuid.UUID,
    event_type: str,
    severity: str,
    message: str,
    details: str,
):
    """Log a security event."""
    event = SecurityEvent(
        upload_id=upload_id,
        event_type=event_type,
        severity=severity,
        message=message,
        details=details,
    )
    db.add(event)
    await db.commit()
