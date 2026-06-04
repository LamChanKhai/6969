"""Pydantic schemas for request/response validation."""

import uuid
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.models import UserRole


# ── Auth ──────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=150)
    password: str = Field(..., min_length=1)


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=150)
    email: EmailStr
    password: str = Field(..., min_length=8)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str


# ── User ──────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=150)
    email: EmailStr
    password: str = Field(..., min_length=8)
    role: UserRole = UserRole.VIEWER


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    id: uuid.UUID
    username: str
    email: str
    role: UserRole
    is_active: bool
    last_login_at: Optional[datetime] = None
    login_attempts: int = 0
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class UserListResponse(BaseModel):
    items: List[UserResponse]
    total: int
    skip: int
    limit: int


# ── File Upload ────────────────────────────────────────────────────────────

class FileUploadResponse(BaseModel):
    id: uuid.UUID
    original_filename: str
    file_size: int
    mime_type: str
    extracted: bool
    extraction_status: str
    security_scan_status: str
    security_scan_result: str
    file_hash_sha256: Optional[str] = None
    archived: bool = False
    archived_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class FileUploadListResponse(BaseModel):
    items: List[FileUploadResponse]
    total: int
    skip: int
    limit: int


class ExtractionStatusResponse(BaseModel):
    upload_id: uuid.UUID
    status: str
    events: list
    created_at: datetime


# ── File Scan Results ─────────────────────────────────────────────────────

class FileScanResultCreate(BaseModel):
    upload_id: uuid.UUID
    scanner_name: str
    scanner_version: Optional[str] = None
    scan_type: str
    scan_status: str = "pending"
    threats_found: int = 0
    scan_details: Optional[str] = None
    duration_ms: Optional[int] = None


class FileScanResultResponse(BaseModel):
    id: uuid.UUID
    upload_id: uuid.UUID
    scanner_name: str
    scanner_version: Optional[str] = None
    scan_type: str
    scan_status: str
    threats_found: int
    scan_details: Optional[str] = None
    duration_ms: Optional[int] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class FileScanResultListResponse(BaseModel):
    items: List[FileScanResultResponse]
    total: int
    skip: int
    limit: int


# ── Rate Limit Events ─────────────────────────────────────────────────────

class RateLimitEventResponse(BaseModel):
    id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    ip_address: str
    endpoint: str
    request_count: int
    window_start: datetime
    window_end: datetime
    action_taken: str
    created_at: datetime

    model_config = {"from_attributes": True}


class RateLimitEventListResponse(BaseModel):
    items: List[RateLimitEventResponse]
    total: int
    skip: int
    limit: int


# ── API Keys ───────────────────────────────────────────────────────────────

class ApiKeyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    expires_at: Optional[datetime] = None


class ApiKeyResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    key_prefix: str
    name: str
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ApiKeyListResponse(BaseModel):
    items: List[ApiKeyResponse]
    total: int
    skip: int
    limit: int


class ApiKeyWithSecretResponse(BaseModel):
    """Returned only once at creation time."""
    api_key: str
    key: ApiKeyResponse


# ── Audit Log ──────────────────────────────────────────────────────────────

class AuditLogResponse(BaseModel):
    id: uuid.UUID
    action: str
    resource_type: str
    resource_id: Optional[str]
    details: str
    ip_address: Optional[str]
    user_agent: Optional[str]
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AuditLogListResponse(BaseModel):
    items: List[AuditLogResponse]
    total: int
    skip: int
    limit: int


# ── Monitoring ─────────────────────────────────────────────────────────────

class SystemHealthResponse(BaseModel):
    status: str
    version: str
    uptime_seconds: float
    database: str
    storage_path: str
    active_users: int
    total_uploads: int
    total_security_events: int


class MetricsResponse(BaseModel):
    cpu_usage_percent: float
    memory_usage_percent: float
    disk_usage_percent: float
    active_connections: int
    requests_per_minute: float
    avg_response_time_ms: float


class SecurityDashboardResponse(BaseModel):
    total_events: int
    events_by_severity: dict
    events_last_24h: int
    blocked_uploads: int
    active_threats: int
    top_vulnerabilities: list


# ── DevSecOps Pipeline ─────────────────────────────────────────────────────

class PipelineStageResponse(BaseModel):
    id: uuid.UUID
    stage_name: str
    stage_order: int
    description: str
    is_active: bool

    model_config = {"from_attributes": True}


class PipelineRunResponse(BaseModel):
    id: uuid.UUID
    stage_name: str
    run_number: int
    status: str
    started_at: datetime
    finished_at: Optional[datetime]
    duration_seconds: Optional[float]
    logs: str

    model_config = {"from_attributes": True}


class PipelineOverviewResponse(BaseModel):
    stages: List[PipelineStageResponse]
    latest_runs: List[PipelineRunResponse]
    overall_status: str


# ── Common ─────────────────────────────────────────────────────────────────

class ErrorResponse(BaseModel):
    detail: str


class HealthCheckResponse(BaseModel):
    status: str = "ok"
    service: str = "CSCV2025 Secure Platform"


# ── Monthly Budget ─────────────────────────────────────────────────────

class MonthlyBudgetResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    month: str
    upload_limit: int
    upload_count: int
    storage_limit_bytes: int
    storage_used_bytes: int
    api_call_limit: int
    api_call_count: int
    budget_exceeded: bool
    notified_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MonthlyBudgetUpdate(BaseModel):
    upload_limit: Optional[int] = None
    storage_limit_bytes: Optional[int] = None
    api_call_limit: Optional[int] = None


class MonthlyBudgetUsageResponse(BaseModel):
    month: str
    upload_usage: float
    storage_usage: float
    api_call_usage: float
    budget_exceeded: bool
    upload_count: int
    upload_limit: int
    storage_used_bytes: int
    storage_limit_bytes: int
    api_call_count: int
    api_call_limit: int


# ── Notification ─────────────────────────────────────────────────────────

class NotificationResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    message: str
    notification_type: str
    is_read: bool
    read_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificationListResponse(BaseModel):
    items: List[NotificationResponse]
    total: int
    skip: int
    limit: int


class NotificationCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    message: str = Field(..., min_length=1)
    notification_type: str = "info"
