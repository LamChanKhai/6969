"""API key management endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.core.database import get_db
from app.core.deps import get_current_user
from app.services.api_key_service import (
    create_api_key,
    list_api_keys,
    revoke_api_key,
)
from app.schemas.schemas import (
    ApiKeyCreate,
    ApiKeyResponse,
    ApiKeyListResponse,
    ApiKeyWithSecretResponse,
)

router = APIRouter()


@router.post("/", response_model=ApiKeyWithSecretResponse)
async def create_api_key_endpoint(
    payload: ApiKeyCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new API key. The raw key is only returned once."""
    user_id = UUID(current_user["sub"])
    raw_key, key_record = await create_api_key(
        db,
        user_id=user_id,
        name=payload.name,
        expires_at=payload.expires_at,
    )
    return ApiKeyWithSecretResponse(
        api_key=raw_key,
        key=ApiKeyResponse.model_validate(key_record),
    )


@router.get("/", response_model=ApiKeyListResponse)
async def list_api_keys_endpoint(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List API keys for the current user."""
    user_id = UUID(current_user["sub"])
    keys, total = await list_api_keys(db, user_id=user_id, skip=skip, limit=limit)
    return ApiKeyListResponse(
        items=[ApiKeyResponse.model_validate(k) for k in keys],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.delete("/{key_id}")
async def revoke_api_key_endpoint(
    key_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Revoke an API key."""
    user_id = UUID(current_user["sub"])
    key = await revoke_api_key(db, key_id=key_id, user_id=user_id)
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")
    return {"detail": "API key revoked", "key_prefix": key.key_prefix}
