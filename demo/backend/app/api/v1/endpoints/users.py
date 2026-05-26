"""User management endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.core.database import get_db
from app.core.deps import get_current_user, get_current_admin_user
from app.services.user_service import (
    get_user_by_id,
    list_users,
    update_user,
    change_user_password,
)
from app.schemas.schemas import (
    UserResponse,
    UserListResponse,
    UserUpdate,
)

router = APIRouter()


@router.get("/", response_model=UserListResponse)
async def list_users_endpoint(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """List users (admin only)."""
    users, total = await list_users(db, skip=skip, limit=limit)
    return UserListResponse(
        items=[UserResponse.model_validate(u) for u in users],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get user by ID. Users can view their own profile; admins can view any."""
    if str(current_user["sub"]) != str(user_id) and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse.model_validate(user)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user_endpoint(
    user_id: UUID,
    user_update: UserUpdate,
    current_user: dict = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Update user (admin only)."""
    user = await update_user(
        db,
        user_id=user_id,
        email=user_update.email,
        role=user_update.role,
        is_active=user_update.is_active,
    )
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse.model_validate(user)


@router.post("/{user_id}/change-password")
async def change_password(
    user_id: UUID,
    new_password: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Change user password. Users can change their own; admins can change any."""
    if str(current_user["sub"]) != str(user_id) and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    if len(new_password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    success = await change_user_password(db, user_id, new_password)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"detail": "Password changed successfully"}
