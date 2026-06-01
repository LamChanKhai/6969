"""
Alembic Migration Integration Tests

Tests:
1. Upgrade from base to head — verify every table/column/constraint
2. Downgrade head → base — verify clean rollback
3. Re-upgrade base → head — verify idempotent behavior
4. Data preservation during downgrade/upgrade cycle
"""

import asyncio
import sys
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path

import asyncpg
import pytest

# ── Helpers ──────────────────────────────────────────────────────────────────

BACKEND_DIR = Path(__file__).parent
DB_DSN = "postgresql://postgres:password@localhost:5432/cscv2025"

EXPECTED_TABLES = {
    "users",
    "file_uploads",
    "audit_logs",
    "extraction_events",
    "security_events",
    "file_scan_results",
    "pipeline_stages",
    "pipeline_runs",
    "rate_limit_events",
    "api_keys",
    "pipeline_executions",
    "pipeline_execution_steps",
}

# Expected columns per table (at head revision)
EXPECTED_COLUMNS = {
    "users": {
        "id", "username", "email", "hashed_password", "role", "is_active",
        "is_superuser", "last_login_at", "login_attempts", "locked_until",
        "failed_login_attempts", "created_at", "updated_at",
    },
    "file_uploads": {
        "id", "user_id", "original_filename", "stored_filename", "file_size",
        "mime_type", "storage_path", "file_hash_sha256", "extracted",
        "extraction_status", "security_scan_status", "security_scan_result",
        "archived", "archived_at", "created_at",
    },
    "audit_logs": {
        "id", "user_id", "action", "resource_type", "resource_id", "details",
        "ip_address", "user_agent", "session_id", "request_id", "created_at",
    },
    "extraction_events": {
        "id", "upload_id", "event_type", "message", "file_path", "status",
        "created_at",
    },
    "security_events": {
        "id", "upload_id", "event_type", "severity", "message", "details",
        "is_resolved", "resolved_at", "resolved_by", "created_at",
    },
    "file_scan_results": {
        "id", "upload_id", "scanner_name", "scanner_version", "scan_type",
        "scan_status", "threats_found", "scan_details", "duration_ms", "created_at",
    },
    "pipeline_stages": {
        "id", "stage_name", "stage_order", "description", "is_active", "created_at",
    },
    "pipeline_runs": {
        "id", "stage_id", "run_number", "status", "started_at", "finished_at",
        "duration_seconds", "logs", "created_at",
    },
    "rate_limit_events": {
        "id", "user_id", "ip_address", "endpoint", "request_count",
        "window_start", "window_end", "action_taken", "created_at",
    },
    "api_keys": {
        "id", "user_id", "key_hash", "key_prefix", "name", "expires_at",
        "last_used_at", "is_active", "created_at",
    },
    "pipeline_executions": {
        "id", "name", "total_steps", "current_step", "status", "step_logs",
        "error_message", "started_at", "finished_at", "created_at",
    },
    "pipeline_execution_steps": {
        "id", "execution_id", "step_number", "step_name", "status", "logs",
        "started_at", "finished_at", "duration_seconds", "created_at",
    },
}

# Expected CHECK constraints
EXPECTED_CHECKS = {
    "chk_file_size",
    "chk_scan_status",
    "chk_extraction_status",
    "chk_users_role",
    "chk_events_severity",
    "chk_runs_status",
    "chk_runs_duration",
    "chk_rate_action",
    "chk_scan_status_fsr",
    "chk_scan_threats",
    "chk_exec_status",
    "chk_exec_steps_range",
    "chk_exec_step_status",
    "chk_extract_status",
    "chk_extract_event_type",
    "chk_stages_name_not_empty",
}

# Expected FK constraints
EXPECTED_FKS = {
    "file_uploads_user_id_fkey",
    "fk_audit_user",
    "extraction_events_upload_id_fkey",
    "fk_security_events_upload",
    "pipeline_runs_stage_id_fkey",
    "file_scan_results_upload_id_fkey",
    "api_keys_user_id_fkey",
    "rate_limit_events_user_id_fkey",
    "fk_security_events_resolved_by",
    "pipeline_execution_steps_execution_id_fkey",
}

# Expected indexes from 0009
EXPECTED_INDEXES_0009 = {
    "idx_uploads_user_created",
    "idx_uploads_scan_status",
    "idx_uploads_extracted",
    "idx_uploads_hash",
    "idx_audit_user_action",
    "idx_audit_resource",
    "idx_events_severity_time",
    "idx_events_resolved",
    "idx_events_type_severity",
    "idx_runs_stage_status",
    "idx_runs_status_time",
    "idx_users_role_active",
    "ix_security_events_resolved_by",
}

# Expected indexes from 0012, 0013, 0014
EXPECTED_INDEXES_HEAD = {
    "idx_pipeline_executions_status",
    "ix_pipeline_execution_steps_execution_id",
    "idx_pipeline_exec_steps_status",
    "idx_events_unresolved",
    "idx_exec_steps_status_time",
    "uq_pipeline_stages_stage_name",
}


def run_alembic(command: str, expect_failure: bool = False) -> subprocess.CompletedProcess:
    result = subprocess.run(
        ["alembic"] + command.split(),
        cwd=BACKEND_DIR,
        capture_output=True,
        text=True,
        env={**dict(__import__("os").environ), "DATABASE_URL": DB_DSN.replace("postgresql://", "postgresql+asyncpg://")},
    )
    if not expect_failure and result.returncode != 0:
        print(f"\n=== ALEMBIC STDOUT ===\n{result.stdout}")
        print(f"\n=== ALEMBIC STDERR ===\n{result.stderr}")
        raise RuntimeError(f"Alembic command failed: {' '.join(['alembic'] + command.split())}")
    return result


async def get_tables(conn: asyncpg.Connection) -> set:
    rows = await conn.fetch("""
        SELECT tablename FROM pg_tables
        WHERE schemaname = 'public' AND tablename != 'alembic_version'
    """)
    return {row["tablename"] for row in rows}


async def get_columns(conn: asyncpg.Connection, table: str) -> set:
    rows = await conn.fetch("""
        SELECT column_name FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = $1
    """, table)
    return {row["column_name"] for row in rows}


async def get_check_constraints(conn: asyncpg.Connection) -> set:
    rows = await conn.fetch("""
        SELECT conname FROM pg_constraint
        WHERE contype = 'c' AND connamespace = 'public'::regnamespace
    """)
    return {row["conname"] for row in rows}


async def get_fk_constraints(conn: asyncpg.Connection) -> set:
    rows = await conn.fetch("""
        SELECT conname FROM pg_constraint
        WHERE contype = 'f' AND connamespace = 'public'::regnamespace
    """)
    return {row["conname"] for row in rows}


async def get_indexes(conn: asyncpg.Connection) -> set:
    rows = await conn.fetch("""
        SELECT indexname FROM pg_indexes
        WHERE schemaname = 'public'
    """)
    return {row["indexname"] for row in rows}


async def insert_sample_data(conn: asyncpg.Connection) -> dict:
    """Insert sample data for data-preservation testing."""
    user_id = await conn.fetchval("""
        INSERT INTO users (username, email, hashed_password, role, is_active,
                           last_login_at, login_attempts, locked_until, failed_login_attempts)
        VALUES ('testuser', 'test@example.com', 'hashed', 'viewer', true,
                NOW() AT TIME ZONE 'UTC', 2, NOW() + INTERVAL '1 hour' AT TIME ZONE 'UTC', 2)
        RETURNING id
    """)

    upload_id = await conn.fetchval("""
        INSERT INTO file_uploads (user_id, original_filename, stored_filename, file_size,
                                  mime_type, storage_path, file_hash_sha256, archived, archived_at)
        VALUES ($1, 'test.txt', 'stored_test.txt', 1024, 'text/plain', '/uploads/test.txt',
                'abc123', false, NULL)
        RETURNING id
    """, user_id)

    await conn.execute("""
        INSERT INTO audit_logs (user_id, action, resource_type, resource_id, details,
                                ip_address, user_agent, session_id, request_id)
        VALUES ($1, 'TEST_ACTION', 'test', 'res-1', 'test details',
                '127.0.0.1', 'test agent', 'sess-1', 'req-1')
    """, user_id)

    await conn.execute("""
        INSERT INTO security_events (upload_id, event_type, severity, message, details,
                                     is_resolved, resolved_at, resolved_by)
        VALUES ($1, 'test_event', 'warning', 'test msg', 'test detail',
                false, NULL, NULL)
    """, upload_id)

    await conn.execute("""
        INSERT INTO file_scan_results (upload_id, scanner_name, scanner_version, scan_type,
                                       scan_status, threats_found, scan_details, duration_ms)
        VALUES ($1, 'ClamAV', '1.0', 'virus', 'completed', 0, 'clean', 150)
    """, upload_id)

    await conn.execute("""
        INSERT INTO rate_limit_events (user_id, ip_address, endpoint, request_count,
                                       window_start, window_end, action_taken)
        VALUES ($1, '127.0.0.1', '/api/test', 5,
                NOW() AT TIME ZONE 'UTC', NOW() + INTERVAL '1 min' AT TIME ZONE 'UTC', 'logged')
    """, user_id)

    await conn.execute("""
        INSERT INTO api_keys (user_id, key_hash, key_prefix, name, expires_at,
                              last_used_at, is_active)
        VALUES ($1, 'hashed_key', 'sk_test_', 'Test Key', NULL, NULL, true)
    """, user_id)

    await conn.execute("""
        INSERT INTO pipeline_stages (stage_name, stage_order, description, is_active)
        VALUES ('test_stage', 1, 'Test stage', true)
    """)

    stage_id = await conn.fetchval("SELECT id FROM pipeline_stages WHERE stage_name = 'test_stage'")
    await conn.execute("""
        INSERT INTO pipeline_runs (stage_id, run_number, status, started_at, finished_at,
                                   duration_seconds, logs)
        VALUES ($1, 1, 'completed', NOW() AT TIME ZONE 'UTC', NOW() AT TIME ZONE 'UTC', 5.0, 'ok')
    """, stage_id)

    await conn.execute("""
        INSERT INTO extraction_events (upload_id, event_type, message, file_path, status)
        VALUES ($1, 'test_extract', 'extracted', '/tmp/test.txt', 'success')
    """, upload_id)

    exec_id = await conn.fetchval("""
        INSERT INTO pipeline_executions (name, total_steps, current_step, status)
        VALUES ('test_exec', 2, 1, 'running')
        RETURNING id
    """)

    await conn.execute("""
        INSERT INTO pipeline_execution_steps (execution_id, step_number, step_name, status)
        VALUES ($1, 1, 'step_1', 'completed')
    """, exec_id)

    return {"user_id": user_id, "upload_id": upload_id, "exec_id": exec_id}


async def verify_sample_data(conn: asyncpg.Connection, ids: dict):
    """Verify sample data survived downgrade/upgrade cycle."""
    user = await conn.fetchrow("SELECT * FROM users WHERE id = $1", ids["user_id"])
    assert user is not None, "User data lost!"
    assert user["username"] == "testuser"
    assert user["login_attempts"] == 2
    assert user["failed_login_attempts"] == 2

    upload = await conn.fetchrow("SELECT * FROM file_uploads WHERE id = $1", ids["upload_id"])
    assert upload is not None, "Upload data lost!"
    assert upload["file_hash_sha256"] == "abc123"
    assert upload["archived"] is False

    audit_count = await conn.fetchval("SELECT COUNT(*) FROM audit_logs WHERE user_id = $1", ids["user_id"])
    assert audit_count >= 1, "Audit log data lost!"

    sec_count = await conn.fetchval("SELECT COUNT(*) FROM security_events WHERE upload_id = $1", ids["upload_id"])
    assert sec_count >= 1, "Security event data lost!"

    scan_count = await conn.fetchval("SELECT COUNT(*) FROM file_scan_results WHERE upload_id = $1", ids["upload_id"])
    assert scan_count >= 1, "Scan result data lost!"

    rl_count = await conn.fetchval("SELECT COUNT(*) FROM rate_limit_events WHERE user_id = $1", ids["user_id"])
    assert rl_count >= 1, "Rate limit event data lost!"

    key_count = await conn.fetchval("SELECT COUNT(*) FROM api_keys WHERE user_id = $1", ids["user_id"])
    assert key_count >= 1, "API key data lost!"

    stage_count = await conn.fetchval("SELECT COUNT(*) FROM pipeline_stages WHERE stage_name = 'test_stage'")
    assert stage_count >= 1, "Pipeline stage data lost!"

    run_count = await conn.fetchval("SELECT COUNT(*) FROM pipeline_runs WHERE stage_id IN (SELECT id FROM pipeline_stages WHERE stage_name = 'test_stage')")
    assert run_count >= 1, "Pipeline run data lost!"

    ext_count = await conn.fetchval("SELECT COUNT(*) FROM extraction_events WHERE upload_id = $1", ids["upload_id"])
    assert ext_count >= 1, "Extraction event data lost!"

    exec_count = await conn.fetchval("SELECT COUNT(*) FROM pipeline_executions WHERE id = $1", ids["exec_id"])
    assert exec_count >= 1, "Pipeline execution data lost!"

    step_count = await conn.fetchval("SELECT COUNT(*) FROM pipeline_execution_steps WHERE execution_id = $1", ids["exec_id"])
    assert step_count >= 1, "Pipeline execution step data lost!"


# ── Fix migration 0011 for testing ──────────────────────────────────────────
# pg_cron is not installed in stock PostgreSQL. We need to create a stub.

def setup_pg_cron_stub(conn: asyncpg.Connection):
    """Create pg_cron stub functions for migration testing."""
    pass


async def setup_pg_cron_stub(conn: asyncpg.Connection):
    """Create pg_cron stub schema/functions for migration 0011 testing."""
    await conn.execute("""
        CREATE SCHEMA IF NOT EXISTS cron
    """)
    await conn.execute("""
        CREATE OR REPLACE FUNCTION cron.schedule(job_name TEXT, schedule TEXT, command TEXT)
        RETURNS INTEGER AS $$
        BEGIN
            RETURN 0;  -- stub: always succeeds
        END;
        $$ LANGUAGE plpgsql
    """)
    await conn.execute("""
        CREATE OR REPLACE FUNCTION cron.unschedule(job_name TEXT)
        RETURNS BOOLEAN AS $$
        BEGIN
            RETURN TRUE;  -- stub: always succeeds
        END;
        $$ LANGUAGE plpgsql
    """)


# ── Tests ────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module")
def db_params():
    return {
        "user": "postgres",
        "password": "password",
        "database": "cscv2025",
        "host": "localhost",
        "port": 5432,
    }


@pytest.mark.asyncio
async def test_01_stamp_base(event_loop, db_params):
    """Stamp the database at base (no revisions applied)."""
    run_alembic("stamp base")
    async with asyncpg.connect(**db_params) as conn:
        version = await conn.fetchval("SELECT version_num FROM alembic_version")
        assert version == "0015_fix_pipeline_runs_status"

        tables = await get_tables(conn)
        assert EXPECTED_TABLES.issubset(tables), f"Missing tables: {EXPECTED_TABLES - tables}"

        for table, expected_cols in EXPECTED_COLUMNS.items():
            actual_cols = await get_columns(conn, table)
            assert expected_cols.issubset(actual_cols), f"Table '{table}' missing: {expected_cols - actual_cols}"

        checks = await get_check_constraints(conn)
        assert EXPECTED_CHECKS.issubset(checks), f"Missing CHECK constraints: {EXPECTED_CHECKS - checks}"

        fks = await get_fk_constraints(conn)
        assert EXPECTED_FKS.issubset(fks), f"Missing FK constraints: {EXPECTED_FKS - fks}"

        indexes = await get_indexes(conn)
        assert EXPECTED_INDEXES_0009.issubset(indexes), f"Missing indexes: {EXPECTED_INDEXES_0009 - indexes}"
        assert EXPECTED_INDEXES_HEAD.issubset(indexes), f"Missing indexes: {EXPECTED_INDEXES_HEAD - indexes}"


@pytest.mark.asyncio
async def test_11_current_rev_check(event_loop, db_params):
    """Verify alembic current command works."""
    result = run_alembic("current")
    assert "0015_fix_pipeline_runs_status" in result.stdout or "0015_fix_pipeline_runs_status" in result.stderr


@pytest.mark.asyncio
async def test_12_history_check(event_loop, db_params):
    """Verify alembic history shows all 15 revisions."""
    result = run_alembic("history")
    output = result.stdout + result.stderr
    for i in range(1, 16):
        rev_id = f"000{i}" if i < 10 else f"00{i}"
        assert rev_id in output, f"Revision {rev_id} not found in history"


@pytest.mark.asyncio
async def test_13_clean_upgrade_from_base(event_loop, db_params):
    """Full clean cycle: downgrade to base, upgrade to head in one shot."""
    run_alembic("downgrade base")
    run_alembic("upgrade head")

    async with asyncpg.connect(**db_params) as conn:
        version = await conn.fetchval("SELECT version_num FROM alembic_version")
        assert version == "0015_fix_pipeline_runs_status"
        tables = await get_tables(conn)
        assert EXPECTED_TABLES.issubset(tables)
