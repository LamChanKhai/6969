"""Audit log endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_admin_user
from app.services.audit_service import list_audit_logs
from app.schemas.schemas import AuditLogResponse, AuditLogListResponse

router = APIRouter()


@router.get("/", response_model=AuditLogListResponse)
async def list_audit_logs_endpoint(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    action: str = Query(None),
    resource_type: str = Query(None),
    current_user: dict = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """List audit logs (admin only)."""
    logs, total = await list_audit_logs(
        db,
        skip=skip,
        limit=limit,
        action=action,
        resource_type=resource_type,
    )
    return AuditLogListResponse(
        items=[AuditLogResponse.model_validate(log) for log in logs],
        total=total,
        skip=skip,
        limit=limit,
    )
