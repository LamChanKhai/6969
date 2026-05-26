"""User model with role-based access control."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Boolean, DateTime, Enum as SAEnum, func
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
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    uploads: Mapped[list["FileUpload"]] = relationship(back_populates="user")
    audit_logs: Mapped[list["AuditLog"]] = relationship(back_populates="user")

    def __repr__(self) -> str:
        return f"<User {self.username} ({self.role})>"


class FileUpload(Base):
    __tablename__ = "file_uploads"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    original_filename: Mapped[str] = mapped_column(String(500))
    stored_filename: Mapped[str] = mapped_column(String(500))
    file_size: Mapped[int] = mapped_column(nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100))
    storage_path: Mapped[str] = mapped_column(String(1000))
    extracted: Mapped[bool] = mapped_column(Boolean, default=False)
    extraction_status: Mapped[str] = mapped_column(
        String(50), default="pending"
    )
    security_scan_status: Mapped[str] = mapped_column(
        String(50), default="pending"
    )
    security_scan_result: Mapped[str] = mapped_column(
        String(200), default=""
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

    def __repr__(self) -> str:
        return f"<FileUpload {self.original_filename}>"


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True, index=True
    )
    action: Mapped[str] = mapped_column(String(100))
    resource_type: Mapped[str] = mapped_column(String(100))
    resource_id: Mapped[str] = mapped_column(String(200), nullable=True)
    details: Mapped[str] = mapped_column(String(1000), default="")
    ip_address: Mapped[str] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    user: Mapped["User"] = relationship(back_populates="audit_logs")

    def __repr__(self) -> str:
        return f"<AuditLog {self.action}>"


class ExtractionEvent(Base):
    __tablename__ = "extraction_events"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    upload_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), nullable=False, index=True
    )
    event_type: Mapped[str] = mapped_column(String(50))
    message: Mapped[str] = mapped_column(String(500), default="")
    file_path: Mapped[str] = mapped_column(String(1000), nullable=True)
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
    upload_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True, index=True
    )
    event_type: Mapped[str] = mapped_column(String(50))
    severity: Mapped[str] = mapped_column(String(20), default="info")
    message: Mapped[str] = mapped_column(String(500), default="")
    details: Mapped[str] = mapped_column(String(2000), default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    upload: Mapped["FileUpload"] = relationship(back_populates="security_events")

    def __repr__(self) -> str:
        return f"<SecurityEvent {self.event_type} ({self.severity})>"


class PipelineStage(Base):
    __tablename__ = "pipeline_stages"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    stage_name: Mapped[str] = mapped_column(String(100))
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
        PG_UUID(as_uuid=True), nullable=False, index=True
    )
    run_number: Mapped[int] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="running")
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    finished_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    duration_seconds: Mapped[float] = mapped_column(nullable=True)
    logs: Mapped[str] = mapped_column(String(5000), default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    stage: Mapped["PipelineStage"] = relationship(back_populates="runs")

    def __repr__(self) -> str:
        return f"<PipelineRun #{self.run_number} ({self.status})>"
