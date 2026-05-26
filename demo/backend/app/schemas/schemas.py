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


# ── Audit Log ──────────────────────────────────────────────────────────────

class AuditLogResponse(BaseModel):
    id: uuid.UUID
    action: str
    resource_type: str
    resource_id: Optional[str]
    details: str
    ip_address: Optional[str]
    user_agent: Optional[str]
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
