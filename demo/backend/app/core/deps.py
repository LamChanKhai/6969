"""Authentication dependency for FastAPI endpoints."""

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_token, verify_token_type

security_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Extract and validate the current user from JWT token."""
    payload = decode_token(credentials.credentials)
    verify_token_type(payload, "access")
    return payload


async def get_current_admin_user(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Require admin or superuser role."""
    if current_user.get("role") not in ("admin",) and not current_user.get("is_superuser"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user


async def get_current_viewer_or_higher(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Require viewer, operator, or admin role."""
    if current_user.get("role") not in ("viewer", "operator", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Viewer or higher privileges required",
        )
    return current_user


async def get_current_operator_or_higher(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Require operator or admin role."""
    if current_user.get("role") not in ("operator", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operator or higher privileges required",
        )
    return current_user
