"""Seed the database with demo data."""

import asyncio
import uuid
from datetime import datetime, timezone, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import engine, async_session_factory, init_db, Base
from app.models.models import (
    User, FileUpload, AuditLog, SecurityEvent,
    ExtractionEvent, PipelineStage, PipelineRun,
    UserRole,
)
from app.core.password import hash_password


async def seed():
    """Populate database with realistic demo data."""
    await init_db()

    async with async_session_factory() as db:
        # ── Users ──────────────────────────────────────────────────────
        admin = User(
            id=uuid.UUID("a1000000-0000-0000-0000-000000000001"),
            username="admin",
            email="admin@cscv2025.demo",
            hashed_password=hash_password("Admin123!"),
            role=UserRole.ADMIN,
            is_superuser=True,
            is_active=True,
            created_at=datetime(2025, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
        )
        db.add(admin)

        operator = User(
            id=uuid.UUID("a1000000-0000-0000-0000-000000000002"),
            username="operator",
            email="operator@cscv2025.demo",
            hashed_password=hash_password("Operator123!"),
            role=UserRole.OPERATOR,
            is_active=True,
            created_at=datetime(2025, 1, 15, 9, 0, 0, tzinfo=timezone.utc),
        )
        db.add(operator)

        viewer = User(
            id=uuid.UUID("a1000000-0000-0000-0000-000000000003"),
            username="viewer",
            email="viewer@cscv2025.demo",
            hashed_password=hash_password("Viewer123!"),
            role=UserRole.VIEWER,
            is_active=True,
            created_at=datetime(2025, 2, 1, 8, 0, 0, tzinfo=timezone.utc),
        )
        db.add(viewer)

        # ── File Uploads ──────────────────────────────────────────────
        upload_ids = []
        upload_data = [
            (operator.id, "report_q1.pdf", "report_q1.pdf", 2048576, "application/pdf", "passed", "not_applicable", "Scanned OK"),
            (operator.id, "data_export.zip", "data_export.zip", 15728640, "application/zip", "passed", "completed", "Archive validated, 12 files extracted"),
            (viewer.id, "presentation.pptx", "presentation.pptx", 5242880, "application/vnd.openxmlformats-officedocument.presentationml.presentation", "passed", "not_applicable", "Scanned OK"),
            (operator.id, "malicious_payload.exe", "blocked_1.exe", 4096, "application/octet-stream", "blocked", "blocked", "Blocked: dangerous file extension"),
            (viewer.id, "traversal_attempt.zip", "blocked_2.zip", 8192, "application/zip", "blocked", "blocked", "Blocked: path traversal detected in entry: ../../etc/passwd"),
            (operator.id, "financial_data.xlsx", "financial_data.xlsx", 3145728, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "passed", "not_applicable", "Scanned OK"),
            (viewer.id, "images_archive.zip", "images_archive.zip", 10485760, "application/zip", "passed", "completed", "Archive validated, 45 files extracted"),
            (operator.id, "config_backup.zip", "config_backup.zip", 102400, "application/zip", "passed", "completed", "Archive validated, 5 files extracted"),
        ]

        for i, (uid, orig, stored, size, mime, scan, extract, result) in enumerate(upload_data, 1):
            upload_id = uuid.UUID(f"a2000000-0000-0000-0000-{i:012d}")
            upload = FileUpload(
                id=upload_id,
                user_id=uid,
                original_filename=orig,
                stored_filename=stored,
                file_size=size,
                mime_type=mime,
                storage_path=f"/storage/{uid}/{stored}",
                extracted=(extract == "completed"),
                extraction_status=extract,
                security_scan_status=scan,
                security_scan_result=result,
                created_at=datetime(2025, 3, 10 + i, 14, 30, 0, tzinfo=timezone.utc),
            )
            db.add(upload)
            upload_ids.append(upload_id)

        # ── Extraction Events ─────────────────────────────────────────
        extraction_events = [
            (upload_ids[1], "extraction_started", "Extracting archive in sandbox", "/storage/sandbox", "success"),
            (upload_ids[1], "file_extracted", "Extracted: report_data.csv", "/storage/sandbox/report_data.csv", "success"),
            (upload_ids[1], "file_extracted", "Extracted: summary.pdf", "/storage/sandbox/summary.pdf", "success"),
            (upload_ids[1], "extraction_completed", "Extracted 12 files", "/storage/sandbox", "success"),
            (upload_ids[6], "extraction_started", "Extracting archive in sandbox", "/storage/sandbox", "success"),
            (upload_ids[6], "extraction_completed", "Extracted 45 files", "/storage/sandbox", "success"),
            (upload_ids[7], "extraction_started", "Extracting archive in sandbox", "/storage/sandbox", "success"),
            (upload_ids[7], "extraction_completed", "Extracted 5 files", "/storage/sandbox", "success"),
        ]

        for i, (uid, etype, msg, fpath, status) in enumerate(extraction_events, 1):
            event = ExtractionEvent(
                id=uuid.UUID(f"a3000000-0000-0000-0000-{i:012d}"),
                upload_id=uid,
                event_type=etype,
                message=msg,
                file_path=fpath,
                status=status,
                created_at=datetime(2025, 3, 10 + i, 14, 35, 0, tzinfo=timezone.utc),
            )
            db.add(event)

        # ── Security Events ───────────────────────────────────────────
        security_events = [
            (upload_ids[3], "blocked_extension", "critical", "Blocked dangerous file type: .exe", "File extension .exe is in the blocked list"),
            (upload_ids[4], "path_traversal_blocked", "critical", "Blocked path traversal attempt: ../../etc/passwd", "ZIP entry contains path traversal sequence"),
            (upload_ids[0], "scan_passed", "info", "File passed security scan", "No threats detected"),
            (upload_ids[1], "scan_passed", "info", "Archive passed security scan", "All entries validated"),
            (upload_ids[2], "scan_passed", "info", "File passed security scan", "No threats detected"),
            (None, "login_attempt", "warning", "Failed login attempt from 192.168.1.100", "Invalid credentials for user 'test'"),
            (None, "login_attempt", "warning", "Failed login attempt from 10.0.0.55", "Invalid credentials for user 'root'"),
            (None, "rate_limit_exceeded", "medium", "Rate limit exceeded from 172.16.0.10", "100 requests in 60 seconds"),
            (None, "suspicious_scan", "high", "Multiple blocked uploads from single user", "User a1000000-0000-0000-0000-000000000002 had 2 blocked uploads"),
            (None, "system_alert", "info", "Daily security report generated", "Report sent to admin@cscv2025.demo"),
        ]

        for i, (uid, etype, sev, msg, detail) in enumerate(security_events, 1):
            event = SecurityEvent(
                id=uuid.UUID(f"a4000000-0000-0000-0000-{i:012d}"),
                upload_id=uid,
                event_type=etype,
                severity=sev,
                message=msg,
                details=detail,
                created_at=datetime(2025, 3, 10 + (i % 5), 15, 0, 0, tzinfo=timezone.utc),
            )
            db.add(event)

        # ── Audit Logs ────────────────────────────────────────────────
        audit_data = [
            (admin.id, "login", "auth", None, "Admin login", "10.0.0.1"),
            (operator.id, "login", "auth", None, "Operator login", "10.0.0.2"),
            (operator.id, "file_upload", "upload", str(upload_ids[0]), "Uploaded report_q1.pdf", "10.0.0.2"),
            (operator.id, "file_upload", "upload", str(upload_ids[1]), "Uploaded data_export.zip", "10.0.0.2"),
            (viewer.id, "login", "auth", None, "Viewer login", "10.0.0.3"),
            (viewer.id, "file_upload", "upload", str(upload_ids[4]), "Upload blocked: traversal_attempt.zip", "10.0.0.3"),
            (admin.id, "user_update", "user", str(operator.id), "Changed role to operator", "10.0.0.1"),
            (admin.id, "audit_export", "audit", None, "Exported audit logs for Q1", "10.0.0.1"),
        ]

        for i, (uid, action, rtype, rid, detail, ip) in enumerate(audit_data, 1):
            log = AuditLog(
                id=uuid.UUID(f"a5000000-0000-0000-0000-{i:012d}"),
                user_id=uid,
                action=action,
                resource_type=rtype,
                resource_id=rid,
                details=detail,
                ip_address=ip,
                user_agent="Mozilla/5.0",
                created_at=datetime(2025, 3, 10 + (i % 3), 16, 0, 0, tzinfo=timezone.utc),
            )
            db.add(log)

        # ── Pipeline Stages ───────────────────────────────────────────
        stages_data = [
            ("Code Scan", 1, "Static code analysis with SonarQube"),
            ("Dependency Check", 2, "SCA scan for known vulnerabilities (OWASP Dependency-Check)"),
            ("Container Scan", 3, "Container image vulnerability scan (Trivy)"),
            ("Secret Detection", 4, "Detect hardcoded secrets and API keys (GitLeaks)"),
            ("SAST Analysis", 5, "Static Application Security Testing (Semgrep)"),
            ("DAST Analysis", 6, "Dynamic Application Security Testing (OWASP ZAP)"),
            ("Compliance Check", 7, "Policy and compliance verification"),
            ("Deploy", 8, "Deploy to staging/production environment"),
        ]

        stages = []
        for i, (name, order, desc) in enumerate(stages_data, 1):
            stage = PipelineStage(
                id=uuid.UUID(f"a6000000-0000-0000-0000-{i:012d}"),
                stage_name=name,
                stage_order=order,
                description=desc,
                is_active=True,
            )
            db.add(stage)
            stages.append(stage)

        # ── Pipeline Runs ─────────────────────────────────────────────
        run_statuses = [
            ("success", "Scan complete: 0 issues found"),
            ("success", "Scan complete: 0 vulnerable dependencies"),
            ("success", "Scan complete: 0 CVEs found"),
            ("success", "Scan complete: 0 secrets detected"),
            ("success", "Scan complete: 0 high/medium issues"),
            ("running", "In progress: testing 47 endpoints..."),
            ("success", "All 7 policies passed"),
            ("success", "Deployment successful to staging"),
        ]

        for i, (status, logs) in enumerate(run_statuses, 1):
            stage = stages[i - 1]
            started = datetime(2025, 3, 15, 10, 0, 0, tzinfo=timezone.utc)
            run = PipelineRun(
                id=uuid.UUID(f"a7000000-0000-0000-0000-{i:012d}"),
                stage_id=stage.id,
                run_number=1,
                status=status,
                started_at=started,
                finished_at=started + timedelta(minutes=i) if status != "running" else None,
                duration_seconds=i * 60 if status != "running" else None,
                logs=logs,
            )
            db.add(run)

        await db.commit()
        print("Database seeded successfully!")


if __name__ == "__main__":
    asyncio.run(seed())
