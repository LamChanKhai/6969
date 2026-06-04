"""Budget management endpoints."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, get_current_admin_user_user
from app.services.budget_service import (
    get_or_create_monthly_budget,
    get_budget_usage,
    list_notifications,
    mark_notification_read,
    mark_all_notifications_read,
    create_notification,
)
from app.schemas.schemas import (
    MonthlyBudgetResponse,
    MonthlyBudgetUpdate,
    MonthlyBudgetUsageResponse,
    NotificationResponse,
    NotificationListResponse,
    NotificationCreate,
)
from app.models.models import MonthlyBudget

router = APIRouter()


@router.get("/usage", response_model=MonthlyBudgetUsageResponse)
async def get_my_budget_usage(
    month: Optional[str] = Query(None, description="Month in YYYY-MM format"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user's monthly budget usage."""
    user_id = UUID(current_user["sub"])
    usage = await get_budget_usage(db, user_id, month)
    if not usage:
        await get_or_create_monthly_budget(db, user_id, month)
        usage = await get_budget_usage(db, user_id, month)
    return usage


@router.put("/usage", response_model=MonthlyBudgetUsageResponse)
async def update_budget_limits(
    body: MonthlyBudgetUpdate,
    month: Optional[str] = Query(None, description="Month in YYYY-MM format"),
    current_user: dict = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Update budget limits for current month (admin only)."""
    user_id = UUID(current_user["sub"])
    budget = await get_or_create_monthly_budget(db, user_id, month)

    if body.upload_limit is not None:
        budget.upload_limit = body.upload_limit
    if body.storage_limit_bytes is not None:
        budget.storage_limit_bytes = body.storage_limit_bytes
    if body.api_call_limit is not None:
        budget.api_call_limit = body.api_call_limit

    budget.budget_exceeded = False
    budget.notified_at = None
    await db.commit()
    await db.refresh(budget)

    return await get_budget_usage(db, user_id, month)


@router.get("/", response_model=MonthlyBudgetResponse)
async def get_user_budget(
    user_id: UUID = Query(..., description="Target user ID"),
    month: Optional[str] = Query(None, description="Month in YYYY-MM format"),
    current_user: dict = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Get budget details for a specific user (admin only)."""
    budget = await get_or_create_monthly_budget(db, user_id, month)
    return MonthlyBudgetResponse.model_validate(budget)


@router.get("/notifications/", response_model=NotificationListResponse)
async def list_my_notifications(
    is_read: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List notifications for the current user."""
    user_id = UUID(current_user["sub"])
    notifications, total = await list_notifications(
        db, user_id, is_read=is_read, skip=skip, limit=limit
    )
    return NotificationListResponse(
        items=[NotificationResponse.model_validate(n) for n in notifications],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.post("/notifications/{notification_id}/read")
async def mark_read(
    notification_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark a notification as read."""
    user_id = UUID(current_user["sub"])
    notification = await mark_notification_read(db, notification_id, user_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"status": "ok"}


@router.post("/notifications/read-all")
async def mark_all_read(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark all notifications as read."""
    user_id = UUID(current_user["sub"])
    count = await mark_all_notifications_read(db, user_id)
    return {"status": "ok", "updated": count}


@router.post("/notifications/", response_model=NotificationResponse)
async def send_notification(
    body: NotificationCreate,
    current_user: dict = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Send a notification to the current user (admin only)."""
    user_id = UUID(current_user["sub"])
    notification = await create_notification(
        db,
        user_id=user_id,
        title=body.title,
        message=body.message,
        notification_type=body.notification_type,
    )
    return NotificationResponse.model_validate(notification)


@router.get("/notifications/unread-count")
async def get_unread_count(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get count of unread notifications."""
    notifications, total = await list_notifications(
        db, UUID(current_user["sub"]), is_read=False, limit=1
    )
    _, total_unread = await list_notifications(
        db, UUID(current_user["sub"]), is_read=False, skip=0, limit=1
    )
    return {"unread_count": total_unread}
