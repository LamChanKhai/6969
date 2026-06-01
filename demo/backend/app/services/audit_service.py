"""Audit log service."""

from datetime import datetime, timedelta
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import AuditLog


async def create_audit_log(
    db: AsyncSession,
    action: str,
    resource_type: str,
    user_id: Optional[UUID] = None,
    resource_id: Optional[str] = None,
    details: str = "",
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> AuditLog:
    """Create an audit log entry."""
    log = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(log)
    await db.commit()
    await db.refresh(log)
    return log


async def list_audit_logs(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 50,
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
) -> tuple[List[AuditLog], int]:
    """List audit logs with optional filters."""
    query = select(AuditLog)
    count_query = select(func.count(AuditLog.id))

    if action:
        query = query.where(AuditLog.action == action)
        count_query = count_query.where(AuditLog.action == action)

    if resource_type:
        query = query.where(AuditLog.resource_type == resource_type)
        count_query = count_query.where(AuditLog.resource_type == resource_type)

    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    query = query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    logs = result.scalars().all()
    return logs, total


async def count_security_events(db: AsyncSession) -> int:
    """Count total security events."""
    from app.models.models import SecurityEvent
    result = await db.execute(select(func.count(SecurityEvent.id)))
    return result.scalar_one()


async def get_security_events_by_severity(db: AsyncSession) -> dict:
    """Get security events grouped by severity."""
    from app.models.models import SecurityEvent
    from sqlalchemy import text
    result = await db.execute(
        text("SELECT severity, COUNT(*) as cnt FROM security_events GROUP BY severity")
    )
    rows = result.fetchall()
    return {row[0]: row[1] for row in rows}


async def get_security_events_last_24h(db: AsyncSession) -> int:
    """Count security events in last 24 hours."""
    from app.models.models import SecurityEvent
    from datetime import timedelta
    cutoff = datetime.utcnow() - timedelta(hours=24)
    result = await db.execute(
        select(func.count(SecurityEvent.id)).where(SecurityEvent.created_at >= cutoff)
    )
    return result.scalar_one()
