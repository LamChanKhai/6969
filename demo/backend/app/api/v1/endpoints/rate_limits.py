"""Rate limit events endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_admin_user
from app.services.rate_limit_service import list_rate_limit_events
from app.schemas.schemas import RateLimitEventResponse, RateLimitEventListResponse

router = APIRouter()


@router.get("/", response_model=RateLimitEventListResponse)
async def list_rate_limit_events_endpoint(
    ip_address: str = Query(None),
    endpoint: str = Query(None),
    action_taken: str = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: dict = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """List rate limit events (admin only)."""
    events, total = await list_rate_limit_events(
        db,
        ip_address=ip_address,
        endpoint=endpoint,
        action_taken=action_taken,
        skip=skip,
        limit=limit,
    )
    return RateLimitEventListResponse(
        items=[RateLimitEventResponse.model_validate(e) for e in events],
        total=total,
        skip=skip,
        limit=limit,
    )
