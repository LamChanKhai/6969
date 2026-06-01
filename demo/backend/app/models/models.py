"""Database models with role-based access control and security tracking."""

import uuid
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import (
    String,
    Boolean,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    Float,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class UserRole(str, Enum):
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    username: Mapped[str] = mapped_column(String(150), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, values_callable=lambda e: [e.value for e in e]),
        default=UserRole.VIEWER,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    login_attempts: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    uploads: Mapped[list["FileUpload"]] = relationship(back_populates="user")
    audit_logs: Mapped[list["AuditLog"]] = relationship(back_populates="user")
    api_keys: Mapped[list["ApiKey"]] = relationship(back_populates="user")
    resolved_events: Mapped[list["SecurityEvent"]] = relationship(
        back_populates="resolver", foreign_keys="SecurityEvent.resolved_by"
    )

    def __repr__(self) -> str:
        return f"<User {self.username} ({self.role})>"


class FileUpload(Base):
    __tablename__ = "file_uploads"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    original_filename: Mapped[str] = mapped_column(String(500))
    stored_filename: Mapped[str] = mapped_column(String(500))
    file_size: Mapped[int] = mapped_column(nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100))
    storage_path: Mapped[str] = mapped_column(String(1000))
    file_hash_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    extracted: Mapped[bool] = mapped_column(Boolean, default=False)
    extraction_status: Mapped[str] = mapped_column(String(50), default="pending")
    security_scan_status: Mapped[str] = mapped_column(String(50), default="pending")
    security_scan_result: Mapped[str] = mapped_column(String(200), default="")
    archived: Mapped[bool] = mapped_column(Boolean, default=False)
    archived_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="uploads")
    extraction_events: Mapped[list["ExtractionEvent"]] = relationship(
        back_populates="upload"
    )
    security_events: Mapped[list["SecurityEvent"]] = relationship(
        back_populates="upload"
    )
    scan_results: Mapped[list["FileScanResult"]] = relationship(
        back_populates="upload"
    )

    def __repr__(self) -> str:
        return f"<FileUpload {self.original_filename}>"


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), primary_key=True, server_default=func.now(), index=True
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    action: Mapped[str] = mapped_column(String(100))
    resource_type: Mapped[str] = mapped_column(String(100))
    resource_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    details: Mapped[str] = mapped_column(String(1000), default="")
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    session_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    request_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    user: Mapped["User"] = relationship(back_populates="audit_logs")

    def __repr__(self) -> str:
        return f"<AuditLog {self.action}>"


class ExtractionEvent(Base):
    __tablename__ = "extraction_events"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    upload_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("file_uploads.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(String(50))
    message: Mapped[str] = mapped_column(String(500), default="")
    file_path: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="success")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    upload: Mapped["FileUpload"] = relationship(back_populates="extraction_events")

    def __repr__(self) -> str:
        return f"<ExtractionEvent {self.event_type}>"


class SecurityEvent(Base):
    __tablename__ = "security_events"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), primary_key=True, server_default=func.now(), index=True
    )
    upload_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("file_uploads.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(String(50))
    severity: Mapped[str] = mapped_column(String(20), default="info")
    message: Mapped[str] = mapped_column(String(500), default="")
    details: Mapped[str] = mapped_column(String(2000), default="")
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    resolved_by: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    upload: Mapped["FileUpload"] = relationship(back_populates="security_events")
    resolver: Mapped["User"] = relationship(
        back_populates="resolved_events", foreign_keys=[resolved_by]
    )

    def __repr__(self) -> str:
        return f"<SecurityEvent {self.event_type} ({self.severity})>"


class FileScanResult(Base):
    __tablename__ = "file_scan_results"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    upload_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("file_uploads.id", ondelete="CASCADE"),
        nullable=False,
    )
    scanner_name: Mapped[str] = mapped_column(String(100))
    scanner_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    scan_type: Mapped[str] = mapped_column(String(50))
    scan_status: Mapped[str] = mapped_column(String(20), default="pending")
    threats_found: Mapped[int] = mapped_column(Integer, default=0)
    scan_details: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    upload: Mapped["FileUpload"] = relationship(back_populates="scan_results")

    def __repr__(self) -> str:
        return f"<FileScanResult {self.scanner_name} ({self.scan_status})>"


class PipelineStage(Base):
    __tablename__ = "pipeline_stages"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    stage_name: Mapped[str] = mapped_column(String(100), unique=True)
    stage_order: Mapped[int] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(String(500), default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    runs: Mapped[list["PipelineRun"]] = relationship(back_populates="stage")

    def __repr__(self) -> str:
        return f"<PipelineStage {self.stage_name}>"


class PipelineRun(Base):
    __tablename__ = "pipeline_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    stage_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("pipeline_stages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    run_number: Mapped[int] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="running")
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    duration_seconds: Mapped[float | None] = mapped_column(nullable=True)
    logs: Mapped[str] = mapped_column(String(5000), default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    stage: Mapped["PipelineStage"] = relationship(back_populates="runs")

    def __repr__(self) -> str:
        return f"<PipelineRun #{self.run_number} ({self.status})>"


class RateLimitEvent(Base):
    __tablename__ = "rate_limit_events"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
    )
    ip_address: Mapped[str] = mapped_column(String(45))
    endpoint: Mapped[str] = mapped_column(String(255))
    request_count: Mapped[int] = mapped_column(Integer)
    window_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    window_end: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    action_taken: Mapped[str] = mapped_column(String(50), default="logged")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    def __repr__(self) -> str:
        return f"<RateLimitEvent {self.ip_address} {self.action_taken}>"


class ApiKey(Base):
    __tablename__ = "api_keys"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    key_hash: Mapped[str] = mapped_column(String(255), unique=True)
    key_prefix: Mapped[str] = mapped_column(String(8))
    name: Mapped[str] = mapped_column(String(100))
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="api_keys")

    def __repr__(self) -> str:
        return f"<ApiKey {self.key_prefix}... ({self.name})>"


class PipelineExecution(Base):
    __tablename__ = "pipeline_executions"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(200))
    total_steps: Mapped[int] = mapped_column(Integer, nullable=False)
    current_step: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default="running")
    step_logs: Mapped[str] = mapped_column(Text, default="")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    steps: Mapped[list["PipelineExecutionStep"]] = relationship(back_populates="execution")

    def __repr__(self) -> str:
        return f"<PipelineExecution {self.name} (step {self.current_step}/{self.total_steps})>"


class PipelineExecutionStep(Base):
    __tablename__ = "pipeline_execution_steps"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    execution_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("pipeline_executions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    step_number: Mapped[int] = mapped_column(Integer, nullable=False)
    step_name: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(20), default="pending")
    logs: Mapped[str] = mapped_column(Text, default="")
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    duration_seconds: Mapped[float | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    execution: Mapped["PipelineExecution"] = relationship(back_populates="steps")

    def __repr__(self) -> str:
        return f"<PipelineExecutionStep #{self.step_number} {self.step_name} ({self.status})>"
