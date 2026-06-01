# Handoff Note — Backend Developer Complete

## Completed Changes

### 1. Migration 0014 Downgrade Fix
**File**: `demo/backend/alembic/versions/0014_partition_security_events.py`

The downgrade function was missing index and constraint recreation. Added:
- `idx_events_severity_time` (severity, created_at)
- `idx_events_resolved` (is_resolved, created_at)
- `idx_events_type_severity` (event_type, severity)
- `ix_security_events_resolved_by` (resolved_by)
- `idx_events_unresolved` partial index (created_at DESC WHERE is_resolved = false)
- `chk_events_severity` CHECK constraint (NOT VALID + VALIDATE)

Downgrade now fully restores the pre-partitioning state with all indexes, FKs, and CHECK constraints.

### 2. SQLAlchemy Model Updates
**File**: `demo/backend/app/models/models.py`

- **`PipelineStage.stage_name`**: Added `unique=True` to reflect migration 0013 UNIQUE constraint
- **`SecurityEvent`**: Changed `created_at` to composite PK (`primary_key=True`) alongside `id`, matching partitioned table PK `(id, created_at)` from migration 0014
- **`AuditLog`**: Changed `created_at` to composite PK (`primary_key=True`) alongside `id`, matching partitioned table PK `(id, created_at)` from migration 0011

## Migration Chain (14 steps)
```
0001 → 0002 → 0003 → 0004 → 0005 → 0006 → 0007 → 0008 → 0009 → 0010 → 0011 → 0012 → 0013 → 0014
```

## Important Notes for Downstream Roles
- Partitioned tables (`audit_logs`, `security_events`) use composite PK `(id, created_at)`. Any application code that queries by `id` alone must also include `created_at` conditions.
- The `idx_events_unresolved` partial index is created in migration 0013 AND re-created in 0014 upgrade (since partitioning drops all indexes). This is intentional — migration 0014 re-creates all indexes after table replacement.
- All CHECK constraints use `NOT VALID + VALIDATE` for zero-downtime deployment compatibility.
