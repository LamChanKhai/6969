"""File upload endpoints with security scanning."""

import aiofiles
import mimetypes
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, status, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user, get_current_operator_or_higher
from app.services.upload_service import (
    validate_file_extension,
    validate_mime_type,
    validate_zip_contents,
    extract_archive_sandboxed,
    create_upload_record,
    list_uploads,
    get_upload_with_events,
)
from app.services.audit_service import create_audit_log
from app.services.budget_service import (
    increment_upload_count,
    check_and_notify_budget_exceeded,
    send_budget_warning,
)
from app.schemas.schemas import (
    FileUploadResponse,
    FileUploadListResponse,
    ExtractionStatusResponse,
)

router = APIRouter()


@router.post("/", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    req: Request = None,
    current_user: dict = Depends(get_current_operator_or_higher),
    db: AsyncSession = Depends(get_db),
):
    """Upload a file with security scanning and sandboxed extraction."""
    user_id = UUID(current_user["sub"])

    # Validate file size
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)

    if file_size > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum allowed ({settings.MAX_UPLOAD_SIZE} bytes)",
        )

    if file_size == 0:
        raise HTTPException(status_code=400, detail="Empty file")

    # Validate file extension
    if not validate_file_extension(file.filename):
        raise HTTPException(
            status_code=400,
            detail=f"File type '{os.path.splitext(file.filename)[1]}' is not allowed",
        )

    # Validate MIME type
    mime_type = file.content_type or mimetypes.guess_type(file.filename)[0] or "application/octet-stream"
    if not validate_mime_type(mime_type):
        raise HTTPException(
            status_code=400,
            detail=f"MIME type '{mime_type}' is not allowed",
        )

    # Generate storage paths
    upload_id = uuid.uuid4()
    user_dir = settings.STORAGE_PATH / str(user_id)
    user_dir.mkdir(parents=True, exist_ok=True)

    ext = os.path.splitext(file.filename)[1]
    stored_filename = f"{upload_id}{ext}"
    file_path = user_dir / stored_filename

    # Save file
    async with aiofiles.open(file_path, "wb") as f:
        content = await file.read()
        await f.write(content)

    # Create DB record
    upload = await create_upload_record(
        db,
        user_id=user_id,
        original_filename=file.filename,
        stored_filename=stored_filename,
        file_size=file_size,
        mime_type=mime_type,
        storage_path=str(file_path),
    )

    # Track monthly budget usage
    exceeded, budget = await increment_upload_count(db, user_id, file_size)

    # Send warning if approaching limit (before exceeding)
    if not exceeded:
        await send_budget_warning(db, user_id, budget, threshold=0.8)
    else:
        await check_and_notify_budget_exceeded(db, user_id, budget)

    # Security scan
    upload.security_scan_status = "scanning"
    await db.commit()
    await db.refresh(upload)

    is_valid, scan_result = await validate_zip_contents(file_path, db, upload.id)

    if is_valid:
        upload.security_scan_status = "passed"
        upload.security_scan_result = scan_result

        # Extract if ZIP
        if mime_type in ("application/zip", "application/x-zip-compressed"):
            upload.extraction_status = "extracting"
            await db.commit()

            success, msg = await extract_archive_sandboxed(
                file_path, user_dir, db, upload.id
            )
            upload.extracted = success
            upload.extraction_status = "completed" if success else "failed"
        else:
            upload.extraction_status = "not_applicable"
    else:
        upload.security_scan_status = "blocked"
        upload.security_scan_result = scan_result
        upload.extraction_status = "blocked"

        # Remove blocked file
        if file_path.exists():
            file_path.unlink()

    await db.commit()
    await db.refresh(upload)

    await create_audit_log(
        db,
        action="file_upload",
        resource_type="upload",
        user_id=user_id,
        resource_id=str(upload.id),
        details=f"Uploaded {file.filename} ({upload.security_scan_status})",
        ip_address=req.client.host if req and req.client else None,
    )

    return FileUploadResponse.model_validate(upload)


@router.get("/", response_model=FileUploadListResponse)
async def list_uploaded_files(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List uploaded files. Users see their own; admins see all."""
    if current_user.get("role") == "admin":
        uploads, total = await list_uploads(db, skip=skip, limit=limit)
    else:
        user_id = UUID(current_user["sub"])
        uploads, total = await list_uploads(db, user_id=user_id, skip=skip, limit=limit)

    return FileUploadListResponse(
        items=[FileUploadResponse.model_validate(u) for u in uploads],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/{upload_id}", response_model=FileUploadResponse)
async def get_upload(
    upload_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get upload details by ID."""
    upload = await get_upload_with_events(db, upload_id)
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")

    # Check ownership or admin access
    if str(upload.user_id) != str(current_user["sub"]) and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    return FileUploadResponse.model_validate(upload)


@router.get("/{upload_id}/extraction-status", response_model=ExtractionStatusResponse)
async def get_extraction_status(
    upload_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get extraction status and events for an upload."""
    upload = await get_upload_with_events(db, upload_id)
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")

    if str(upload.user_id) != str(current_user["sub"]) and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    events = [
        {
            "event_type": e.event_type,
            "message": e.message,
            "file_path": e.file_path,
            "status": e.status,
            "created_at": e.created_at.isoformat(),
        }
        for e in upload.extraction_events
    ]

    return ExtractionStatusResponse(
        upload_id=upload.id,
        status=upload.extraction_status,
        events=events,
        created_at=upload.created_at,
    )
