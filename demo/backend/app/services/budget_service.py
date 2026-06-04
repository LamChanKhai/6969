"""Budget tracking and notification service."""

import logging
from datetime import datetime, timezone
from typing import Optional, List, Tuple
from uuid import UUID

from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import MonthlyBudget, Notification, User

logger = logging.getLogger(__name__)


def get_current_month() -> str:
    """Return current month in YYYY-MM format."""
    return datetime.now(timezone.utc).strftime("%Y-%m")


async def get_or_create_monthly_budget(
    db: AsyncSession,
    user_id: UUID,
    month: Optional[str] = None,
) -> MonthlyBudget:
    """Get or create a monthly budget record for a user."""
    if month is None:
        month = get_current_month()

    result = await db.execute(
        select(MonthlyBudget).where(
            MonthlyBudget.user_id == user_id,
            MonthlyBudget.month == month,
        )
    )
    budget = result.scalar_one_or_none()

    if budget:
        return budget

    budget = MonthlyBudget(
        user_id=user_id,
        month=month,
    )
    db.add(budget)
    await db.commit()
    await db.refresh(budget)
    return budget


async def increment_upload_count(
    db: AsyncSession,
    user_id: UUID,
    file_size: int,
) -> Tuple[bool, MonthlyBudget]:
    """Increment upload count and storage used. Returns (budget_exceeded, budget)."""
    month = get_current_month()
    budget = await get_or_create_monthly_budget(db, user_id, month)

    budget.upload_count += 1
    budget.storage_used_bytes += file_size

    # Check if any limit is exceeded
    exceeded = False
    if budget.upload_count > budget.upload_limit:
        exceeded = True
    if budget.storage_used_bytes > budget.storage_limit_bytes:
        exceeded = True
    if budget.api_call_count > budget.api_call_limit:
        exceeded = True

    budget.budget_exceeded = exceeded
    await db.commit()
    await db.refresh(budget)
    return exceeded, budget


async def increment_api_call_count(
    db: AsyncSession,
    user_id: UUID,
) -> Tuple[bool, MonthlyBudget]:
    """Increment API call count. Returns (budget_exceeded, budget)."""
    month = get_current_month()
    budget = await get_or_create_monthly_budget(db, user_id, month)

    budget.api_call_count += 1

    exceeded = False
    if budget.upload_count > budget.upload_limit:
        exceeded = True
    if budget.storage_used_bytes > budget.storage_limit_bytes:
        exceeded = True
    if budget.api_call_count > budget.api_call_limit:
        exceeded = True

    budget.budget_exceeded = exceeded
    await db.commit()
    await db.refresh(budget)
    return exceeded, budget


async def check_and_notify_budget_exceeded(
    db: AsyncSession,
    user_id: UUID,
    budget: MonthlyBudget,
) -> Optional[Notification]:
    """Check if budget was just exceeded and send notification if not yet notified."""
    if not budget.budget_exceeded:
        return None

    if budget.notified_at:
        return None

    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        return None

    reasons = []
    if budget.upload_count > budget.upload_limit:
        reasons.append(
            f"Uploads: {budget.upload_count}/{budget.upload_limit}"
        )
    if budget.storage_used_bytes > budget.storage_limit_bytes:
        used_mb = budget.storage_used_bytes / (1024 * 1024)
        limit_mb = budget.storage_limit_bytes / (1024 * 1024)
        reasons.append(
            f"Storage: {used_mb:.1f}MB/{limit_mb:.1f}MB"
        )
    if budget.api_call_count > budget.api_call_limit:
        reasons.append(
            f"API calls: {budget.api_call_count}/{budget.api_call_limit}"
        )

    reason_str = "; ".join(reasons)

    notification = Notification(
        user_id=user_id,
        title="Monthly Budget Limit Reached",
        message=(
            f"Your monthly budget limit has been reached for {budget.month}. "
            f"Reason: {reason_str}. "
            f"Please contact your administrator to increase your limits or wait until the next billing cycle."
        ),
        notification_type="budget_exceeded",
    )
    db.add(notification)

    budget.notified_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(notification)

    logger.info(
        "Budget exceeded notification sent to user %s for month %s",
        user_id,
        budget.month,
    )
    return notification


async def send_budget_warning(
    db: AsyncSession,
    user_id: UUID,
    budget: MonthlyBudget,
    threshold: float = 0.8,
) -> Optional[Notification]:
    """Send a warning notification when usage approaches the limit."""
    upload_pct = budget.upload_count / budget.upload_limit if budget.upload_limit > 0 else 0
    storage_pct = budget.storage_used_bytes / budget.storage_limit_bytes if budget.storage_limit_bytes > 0 else 0
    api_pct = budget.api_call_count / budget.api_call_limit if budget.api_call_limit > 0 else 0

    max_pct = max(upload_pct, storage_pct, api_pct)
    if max_pct < threshold:
        return None

    warnings = []
    if upload_pct >= threshold:
        warnings.append(f"Uploads at {upload_pct*100:.0f}%")
    if storage_pct >= threshold:
        warnings.append(f"Storage at {storage_pct*100:.0f}%")
    if api_pct >= threshold:
        warnings.append(f"API calls at {api_pct*100:.0f}%")

    warning_str = "; ".join(warnings)

    notification = Notification(
        user_id=user_id,
        title="Monthly Budget Warning",
        message=(
            f"You are approaching your monthly budget limit for {budget.month}. "
            f"Current usage: {warning_str}. "
            f"Please monitor your usage to avoid exceeding your limits."
        ),
        notification_type="budget_warning",
    )
    db.add(notification)
    await db.commit()
    await db.refresh(notification)

    logger.info(
        "Budget warning notification sent to user %s for month %s",
        user_id,
        budget.month,
    )
    return notification


async def get_budget_usage(
    db: AsyncSession,
    user_id: UUID,
    month: Optional[str] = None,
) -> Optional[dict]:
    """Get budget usage percentages for a user."""
    if month is None:
        month = get_current_month()

    result = await db.execute(
        select(MonthlyBudget).where(
            MonthlyBudget.user_id == user_id,
            MonthlyBudget.month == month,
        )
    )
    budget = result.scalar_one_or_none()
    if not budget:
        return None

    return {
        "month": budget.month,
        "upload_usage": (budget.upload_count / budget.upload_limit * 100) if budget.upload_limit > 0 else 0,
        "storage_usage": (budget.storage_used_bytes / budget.storage_limit_bytes * 100) if budget.storage_limit_bytes > 0 else 0,
        "api_call_usage": (budget.api_call_count / budget.api_call_limit * 100) if budget.api_call_limit > 0 else 0,
        "budget_exceeded": budget.budget_exceeded,
        "upload_count": budget.upload_count,
        "upload_limit": budget.upload_limit,
        "storage_used_bytes": budget.storage_used_bytes,
        "storage_limit_bytes": budget.storage_limit_bytes,
        "api_call_count": budget.api_call_count,
        "api_call_limit": budget.api_call_limit,
    }


async def list_notifications(
    db: AsyncSession,
    user_id: UUID,
    is_read: Optional[bool] = None,
    skip: int = 0,
    limit: int = 50,
) -> Tuple[List[Notification], int]:
    """List notifications for a user."""
    query = select(Notification).where(Notification.user_id == user_id)
    count_query = select(func.count(Notification.id)).where(Notification.user_id == user_id)

    if is_read is not None:
        query = query.where(Notification.is_read == is_read)
        count_query = count_query.where(Notification.is_read == is_read)

    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    query = query.order_by(Notification.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    notifications = list(result.scalars().all())
    return notifications, total


async def mark_notification_read(
    db: AsyncSession,
    notification_id: UUID,
    user_id: UUID,
) -> Optional[Notification]:
    """Mark a notification as read."""
    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == user_id,
        )
    )
    notification = result.scalar_one_or_none()
    if not notification:
        return None

    notification.is_read = True
    notification.read_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(notification)
    return notification


async def mark_all_notifications_read(
    db: AsyncSession,
    user_id: UUID,
) -> int:
    """Mark all notifications as read. Returns count of updated notifications."""
    now = datetime.now(timezone.utc)
    stmt = (
        update(Notification)
        .where(
            Notification.user_id == user_id,
            Notification.is_read == False,
        )
        .values(is_read=True, read_at=now)
    )
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount


async def create_notification(
    db: AsyncSession,
    user_id: UUID,
    title: str,
    message: str,
    notification_type: str = "info",
) -> Notification:
    """Create a new notification."""
    notification = Notification(
        user_id=user_id,
        title=title,
        message=message,
        notification_type=notification_type,
    )
    db.add(notification)
    await db.commit()
    await db.refresh(notification)
    return notification
