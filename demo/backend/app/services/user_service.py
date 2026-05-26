"""User service — CRUD operations."""

from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.models import User, UserRole
from app.core.password import hash_password, verify_password


async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
    """Get a user by username."""
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """Get a user by email."""
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: UUID) -> Optional[User]:
    """Get a user by UUID."""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def create_user(
    db: AsyncSession,
    username: str,
    email: str,
    password: str,
    role: UserRole = UserRole.VIEWER,
    is_superuser: bool = False,
) -> User:
    """Create a new user with hashed password."""
    user = User(
        username=username,
        email=email,
        hashed_password=hash_password(password),
        role=role,
        is_superuser=is_superuser,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate_user(db: AsyncSession, username: str, password: str) -> Optional[User]:
    """Authenticate user by username and password."""
    user = await get_user_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    if not user.is_active:
        return None
    return user


async def update_user(
    db: AsyncSession,
    user_id: UUID,
    email: Optional[str] = None,
    role: Optional[UserRole] = None,
    is_active: Optional[bool] = None,
) -> Optional[User]:
    """Update user fields."""
    user = await get_user_by_id(db, user_id)
    if not user:
        return None
    if email is not None:
        user.email = email
    if role is not None:
        user.role = role
    if is_active is not None:
        user.is_active = is_active
    await db.commit()
    await db.refresh(user)
    return user


async def change_user_password(db: AsyncSession, user_id: UUID, new_password: str) -> bool:
    """Change user password."""
    user = await get_user_by_id(db, user_id)
    if not user:
        return False
    user.hashed_password = hash_password(new_password)
    await db.commit()
    return True


async def list_users(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 20,
    role: Optional[UserRole] = None,
    is_active: Optional[bool] = None,
) -> tuple[List[User], int]:
    """List users with optional filters."""
    query = select(User)
    count_query = select(func.count(User.id))

    if role is not None:
        query = query.where(User.role == role)
        count_query = count_query.where(User.role == role)

    if is_active is not None:
        query = query.where(User.is_active == is_active)
        count_query = count_query.where(User.is_active == is_active)

    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    query = query.order_by(User.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    users = result.scalars().all()
    return users, total


async def count_users(db: AsyncSession) -> int:
    """Count active users."""
    result = await db.execute(select(func.count(User.id)).where(User.is_active == True))
    return result.scalar_one()
