"""File scan results endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.core.database import get_db
from app.core.deps import get_current_user, get_current_admin_user, get_current_viewer_or_higher
from app.services.scan_service import (
    create_scan_result,
    list_scan_results,
    get_scan_result,
    update_scan_result,
)
from app.schemas.schemas import (
    FileScanResultCreate,
    FileScanResultResponse,
    FileScanResultListResponse,
)

router = APIRouter()


@router.post("/", response_model=FileScanResultResponse)
async def create_scan_result_endpoint(
    payload: FileScanResultCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a file scan result (operator/admin only)."""
    if current_user.get("role") not in ("admin", "operator"):
        raise HTTPException(status_code=403, detail="Operator or admin required")

    scan = await create_scan_result(
        db,
        upload_id=payload.upload_id,
        scanner_name=payload.scanner_name,
        scan_type=payload.scan_type,
        scanner_version=payload.scanner_version,
        scan_status=payload.scan_status,
        threats_found=payload.threats_found,
        scan_details=payload.scan_details,
        duration_ms=payload.duration_ms,
    )
    return FileScanResultResponse.model_validate(scan)


@router.get("/", response_model=FileScanResultListResponse)
async def list_scan_results_endpoint(
    upload_id: UUID = Query(None),
    scan_type: str = Query(None),
    scan_status: str = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: dict = Depends(get_current_viewer_or_higher),
    db: AsyncSession = Depends(get_db),
):
    """List file scan results."""
    scans, total = await list_scan_results(
        db,
        upload_id=upload_id,
        scan_type=scan_type,
        scan_status=scan_status,
        skip=skip,
        limit=limit,
    )
    return FileScanResultListResponse(
        items=[FileScanResultResponse.model_validate(s) for s in scans],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/{scan_id}", response_model=FileScanResultResponse)
async def get_scan_result_endpoint(
    scan_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single scan result by ID."""
    scan = await get_scan_result(db, scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan result not found")
    return FileScanResultResponse.model_validate(scan)


@router.put("/{scan_id}", response_model=FileScanResultResponse)
async def update_scan_result_endpoint(
    scan_id: UUID,
    scan_status: str = Query(None),
    threats_found: int = Query(None),
    scan_details: str = Query(None),
    duration_ms: int = Query(None),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a scan result (operator/admin only)."""
    if current_user.get("role") not in ("admin", "operator"):
        raise HTTPException(status_code=403, detail="Operator or admin required")

    scan = await update_scan_result(
        db,
        scan_id=scan_id,
        scan_status=scan_status,
        threats_found=threats_found,
        scan_details=scan_details,
        duration_ms=duration_ms,
    )
    if not scan:
        raise HTTPException(status_code=404, detail="Scan result not found")
    return FileScanResultResponse.model_validate(scan)

