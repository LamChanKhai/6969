"""File scan results service."""

from datetime import datetime, timezone
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.models import FileScanResult, FileUpload


async def create_scan_result(
    db: AsyncSession,
    upload_id: UUID,
    scanner_name: str,
    scan_type: str,
    scanner_version: Optional[str] = None,
    scan_status: str = "pending",
    threats_found: int = 0,
    scan_details: Optional[str] = None,
    duration_ms: Optional[int] = None,
) -> FileScanResult:
    """Create a file scan result record."""
    scan = FileScanResult(
        upload_id=upload_id,
        scanner_name=scanner_name,
        scanner_version=scanner_version,
        scan_type=scan_type,
        scan_status=scan_status,
        threats_found=threats_found,
        scan_details=scan_details,
        duration_ms=duration_ms,
    )
    db.add(scan)
    await db.commit()
    await db.refresh(scan)
    return scan


async def update_scan_result(
    db: AsyncSession,
    scan_id: UUID,
    scan_status: Optional[str] = None,
    threats_found: Optional[int] = None,
    scan_details: Optional[str] = None,
    duration_ms: Optional[int] = None,
) -> Optional[FileScanResult]:
    """Update a file scan result."""
    result = await db.execute(
        select(FileScanResult).where(FileScanResult.id == scan_id)
    )
    scan = result.scalar_one_or_none()
    if not scan:
        return None

    if scan_status is not None:
        scan.scan_status = scan_status
    if threats_found is not None:
        scan.threats_found = threats_found
    if scan_details is not None:
        scan.scan_details = scan_details
    if duration_ms is not None:
        scan.duration_ms = duration_ms

    await db.commit()
    await db.refresh(scan)
    return scan


async def list_scan_results(
    db: AsyncSession,
    upload_id: Optional[UUID] = None,
    scan_type: Optional[str] = None,
    scan_status: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
) -> tuple[List[FileScanResult], int]:
    """List file scan results with optional filters."""
    query = select(FileScanResult)
    count_query = select(func.count(FileScanResult.id))

    if upload_id is not None:
        query = query.where(FileScanResult.upload_id == upload_id)
        count_query = count_query.where(FileScanResult.upload_id == upload_id)

    if scan_type is not None:
        query = query.where(FileScanResult.scan_type == scan_type)
        count_query = count_query.where(FileScanResult.scan_type == scan_type)

    if scan_status is not None:
        query = query.where(FileScanResult.scan_status == scan_status)
        count_query = count_query.where(FileScanResult.scan_status == scan_status)

    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    query = query.order_by(FileScanResult.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    scans = result.scalars().all()
    return scans, total


async def get_scan_result(
    db: AsyncSession,
    scan_id: UUID,
) -> Optional[FileScanResult]:
    """Get a single scan result by ID."""
    result = await db.execute(
        select(FileScanResult).where(FileScanResult.id == scan_id)
    )
    return result.scalar_one_or_none()


async def update_upload_scan_status(
    db: AsyncSession,
    upload_id: UUID,
    scan_status: str,
    scan_result: str = "",
) -> Optional[FileUpload]:
    """Update the upload's aggregated scan status after a scan completes."""
    result = await db.execute(
        select(FileUpload).where(FileUpload.id == upload_id)
    )
    upload = result.scalar_one_or_none()
    if not upload:
        return None

    upload.security_scan_status = scan_status
    upload.security_scan_result = scan_result
    await db.commit()
    await db.refresh(upload)
    return upload
