"""Monitoring dashboard endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_viewer_or_higher
from app.services.monitoring_service import get_system_metrics, get_uptime
from app.services.user_service import count_users
from app.services.upload_service import count_uploads, count_blocked_uploads
from app.services.audit_service import (
    count_security_events,
    get_security_events_by_severity,
    get_security_events_last_24h,
)
from app.schemas.schemas import (
    SystemHealthResponse,
    MetricsResponse,
    SecurityDashboardResponse,
)

router = APIRouter()


@router.get("/health", response_model=SystemHealthResponse)
async def system_health(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_viewer_or_higher),
):
    """Get detailed system health information."""
    active_users = await count_users(db)
    total_uploads = await count_uploads(db)
    total_security_events = await count_security_events(db)

    return SystemHealthResponse(
        status="healthy",
        version=settings.APP_VERSION,
        uptime_seconds=get_uptime(),
        database="connected",
        storage_path=str(settings.STORAGE_PATH),
        active_users=active_users,
        total_uploads=total_uploads,
        total_security_events=total_security_events,
    )


@router.get("/metrics", response_model=MetricsResponse)
async def system_metrics(
    current_user: dict = Depends(get_current_viewer_or_higher),
):
    """Get real-time system metrics."""
    metrics = get_system_metrics()
    return MetricsResponse(**metrics)


@router.get("/security-dashboard", response_model=SecurityDashboardResponse)
async def security_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_viewer_or_higher),
):
    """Get security dashboard data."""
    total_events = await count_security_events(db)
    events_by_severity = await get_security_events_by_severity(db)
    events_last_24h = await get_security_events_last_24h(db)
    blocked_uploads = await count_blocked_uploads(db)

    return SecurityDashboardResponse(
        total_events=total_events,
        events_by_severity=events_by_severity,
        events_last_24h=events_last_24h,
        blocked_uploads=blocked_uploads,
        active_threats=events_by_severity.get("critical", 0) + events_by_severity.get("high", 0),
        top_vulnerabilities=[
            {"type": "path_traversal", "count": events_by_severity.get("critical", 0)},
            {"type": "blocked_extension", "count": events_by_severity.get("high", 0)},
            {"type": "invalid_archive", "count": events_by_severity.get("medium", 0)},
        ],
    )
