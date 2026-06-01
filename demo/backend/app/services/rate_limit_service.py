"""Rate limiting service."""

from datetime import datetime, timedelta, timezone
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import RateLimitEvent
from app.core.config import settings


async def check_rate_limit(
    db: AsyncSession,
    ip_address: str,
    endpoint: str,
    user_id: Optional[UUID] = None,
) -> tuple[bool, int]:
    """Check if a request exceeds the rate limit.

    Returns (is_limited, current_count).
    """
    window_start = datetime.now(timezone.utc) - timedelta(minutes=1)

    result = await db.execute(
        select(func.count(RateLimitEvent.id)).where(
            RateLimitEvent.ip_address == ip_address,
            RateLimitEvent.endpoint == endpoint,
            RateLimitEvent.window_start >= window_start,
        )
    )
    current_count = result.scalar_one()

    is_limited = current_count >= settings.RATE_LIMIT_PER_MINUTE
    return is_limited, current_count


async def record_rate_limit_event(
    db: AsyncSession,
    ip_address: str,
    endpoint: str,
    request_count: int,
    user_id: Optional[UUID] = None,
    action_taken: str = "logged",
) -> RateLimitEvent:
    """Record a rate limit event."""
    now = datetime.now(timezone.utc)
    event = RateLimitEvent(
        user_id=user_id,
        ip_address=ip_address,
        endpoint=endpoint,
        request_count=request_count,
        window_start=now - timedelta(minutes=1),
        window_end=now,
        action_taken=action_taken,
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return event


async def list_rate_limit_events(
    db: AsyncSession,
    ip_address: Optional[str] = None,
    endpoint: Optional[str] = None,
    action_taken: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
) -> tuple[List[RateLimitEvent], int]:
    """List rate limit events with optional filters."""
    query = select(RateLimitEvent)
    count_query = select(func.count(RateLimitEvent.id))

    if ip_address is not None:
        query = query.where(RateLimitEvent.ip_address == ip_address)
        count_query = count_query.where(RateLimitEvent.ip_address == ip_address)

    if endpoint is not None:
        query = query.where(RateLimitEvent.endpoint == endpoint)
        count_query = count_query.where(RateLimitEvent.endpoint == endpoint)

    if action_taken is not None:
        query = query.where(RateLimitEvent.action_taken == action_taken)
        count_query = count_query.where(RateLimitEvent.action_taken == action_taken)

    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    query = query.order_by(RateLimitEvent.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    events = result.scalars().all()
    return events, total
