"""API key management service."""

import hashlib
import secrets
import uuid
from datetime import datetime, timezone
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import ApiKey


def generate_api_key() -> str:
    """Generate a random API key."""
    return "cscv_" + secrets.token_urlsafe(32)


def hash_api_key(api_key: str) -> str:
    """Hash an API key for storage."""
    return hashlib.sha256(api_key.encode()).hexdigest()


def get_key_prefix(api_key: str) -> str:
    """Extract the prefix from an API key for display."""
    return api_key[:8]


async def create_api_key(
    db: AsyncSession,
    user_id: UUID,
    name: str,
    expires_at: Optional[datetime] = None,
) -> tuple[str, ApiKey]:
    """Create a new API key. Returns (raw_key, api_key_record).

    The raw key is only returned once at creation time.
    """
    raw_key = generate_api_key()
    key_record = ApiKey(
        user_id=user_id,
        key_hash=hash_api_key(raw_key),
        key_prefix=get_key_prefix(raw_key),
        name=name,
        expires_at=expires_at,
    )
    db.add(key_record)
    await db.commit()
    await db.refresh(key_record)
    return raw_key, key_record


async def validate_api_key(
    db: AsyncSession,
    api_key: str,
) -> Optional[ApiKey]:
    """Validate an API key and return the record if valid."""
    key_hash = hash_api_key(api_key)
    result = await db.execute(
        select(ApiKey).where(
            ApiKey.key_hash == key_hash,
            ApiKey.is_active == True,
        )
    )
    key_record = result.scalar_one_or_none()

    if key_record and key_record.expires_at:
        if key_record.expires_at < datetime.now(timezone.utc):
            return None

    if key_record:
        key_record.last_used_at = datetime.now(timezone.utc)
        await db.commit()

    return key_record


async def list_api_keys(
    db: AsyncSession,
    user_id: UUID,
    skip: int = 0,
    limit: int = 50,
) -> tuple[List[ApiKey], int]:
    """List API keys for a user."""
    query = select(ApiKey).where(ApiKey.user_id == user_id)
    count_query = select(func.count(ApiKey.id)).where(ApiKey.user_id == user_id)

    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    query = query.order_by(ApiKey.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    keys = result.scalars().all()
    return keys, total


async def revoke_api_key(
    db: AsyncSession,
    key_id: UUID,
    user_id: UUID,
) -> Optional[ApiKey]:
    """Revoke an API key."""
    result = await db.execute(
        select(ApiKey).where(
            ApiKey.id == key_id,
            ApiKey.user_id == user_id,
        )
    )
    key_record = result.scalar_one_or_none()
    if not key_record:
        return None

    key_record.is_active = False
    await db.commit()
    await db.refresh(key_record)
    return key_record
