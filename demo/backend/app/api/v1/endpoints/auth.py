"""Authentication endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.core.database import get_db
from app.core.security import create_access_token, create_refresh_token, decode_token, verify_token_type
from app.core.deps import get_current_user
from app.services.user_service import authenticate_user, create_user, get_user_by_username
from app.services.audit_service import create_audit_log
from app.schemas.schemas import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    RefreshRequest,
    UserResponse,
)

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    req: Request,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate user and return JWT tokens."""
    user, reason = await authenticate_user(db, request.username, request.password)
    if not user:
        if reason == "locked":
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="Account is temporarily locked due to too many failed login attempts",
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    token_data = {
        "sub": str(user.id),
        "username": user.username,
        "role": user.role,
        "is_superuser": user.is_superuser,
    }

    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    await create_audit_log(
        db,
        action="login",
        resource_type="auth",
        user_id=user.id,
        details=f"User {user.username} logged in",
        ip_address=req.client.host if req.client else None,
        user_agent=req.headers.get("user-agent"),
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=3600,
    )


@router.post("/register", response_model=UserResponse)
async def register(
    request: RegisterRequest,
    req: Request,
    db: AsyncSession = Depends(get_db),
):
    """Register a new user."""
    existing = await get_user_by_username(db, request.username)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists",
        )

    user = await create_user(
        db,
        username=request.username,
        email=request.email,
        password=request.password,
    )

    await create_audit_log(
        db,
        action="register",
        resource_type="user",
        user_id=user.id,
        details=f"New user registered: {user.username}",
        ip_address=req.client.host if req.client else None,
    )

    return UserResponse.model_validate(user)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    """Refresh access token using refresh token."""
    payload = decode_token(request.refresh_token)
    verify_token_type(payload, "refresh")

    token_data = {
        "sub": payload["sub"],
        "username": payload["username"],
        "role": payload["role"],
        "is_superuser": payload["is_superuser"],
    }

    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=3600,
    )


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current authenticated user profile."""
    from app.services.user_service import get_user_by_id

    user = await get_user_by_id(db, UUID(current_user["sub"]))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse.model_validate(user)
