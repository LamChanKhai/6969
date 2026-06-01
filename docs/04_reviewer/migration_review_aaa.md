## Review Summary

**Type**: Code Review (Alembic Migration Suite)
**Files Reviewed**: 15 migration files (0001-0015), 1 model file, 1 schema design doc
**Overall Assessment**: **Requires Rework** — 3 Critical issues found

---

### Critical Issues

#### Issue 1: security_events archive cron job — substring positions are wrong
- **Location**: `0014_partition_security_events.py:237-238`
- **Severity**: Critical
- **Category**: Bug / Data Loss Risk
- **Description**: The archive cron job parses partition names like `security_events_2026_q1` (23 chars). The code uses `substring(partition_name from 19 for 4)` to extract the year and `substring(partition_name from 24)` for the quarter. The correct offsets are **17** and **23** respectively.

  Character map (1-indexed):
  ```
  security_events_2026_q1
  12345678901234567890123
              1111111111222
  ```
  - `substring(from 19, 4)` → `26_q` (casts to INT → **ERROR**)
  - `substring(from 24)` → `` (empty → **ERROR**)
  - Correct: `substring(from 17, 4)` → `2026`, `substring(from 23)` → `1`

  This means the archive job will **fail silently on every execution**, and old partitions will never be detached. Storage will grow unbounded.

- **Suggestion**: Fix to:
  ```sql
  part_year := substring(partition_name from 17 for 4)::INT;
  part_q := substring(partition_name from 23)::INT;
  ```

#### Issue 2: audit_logs archive cron job — substring position is off by one
- **Location**: `0011_partition_audit_logs.py:151`
- **Severity**: Critical
- **Category**: Bug / Data Loss Risk
- **Description**: The archive cron job parses partition names like `audit_logs_2026_05` (18 chars). The code uses `substring(partition_name from 13)` to extract the date portion, but the year starts at position **12**.

  Character map (1-indexed):
  ```
  audit_logs_2026_05
  123456789012345678
          11111111112
  ```
  - `substring(from 13)` → `026_05` (parsed as `YYYY_MM` → **ERROR**: `to_date('026_05', 'YYYY_MM')` fails)
  - Correct: `substring(from 12)` → `2026_05`

  Same consequence as Issue 1 — archive job fails silently, storage grows unbounded.

- **Suggestion**: Fix to:
  ```sql
  to_date(substring(partition_name from 12), 'YYYY_MM')
  ```

#### Issue 3: security_events downgrade — duplicate CHECK constraint error
- **Location**: `0014_partition_security_events.py:273` and `310-313`
- **Severity**: Critical
- **Category**: Bug / Downgrade Failure
- **Description**: The downgrade creates `security_events_temp` using `LIKE security_events INCLUDING CONSTRAINTS`. The partitioned parent table has the `chk_events_severity` CHECK constraint (added in 0014 Step 8). This constraint is copied to the temp table. After renaming to `security_events`, the downgrade then attempts to add `chk_events_severity` again at line 310, which will fail with `duplicate constraint name`.

  This means **downgrading from 0014 is broken** — you cannot roll back the security_events partitioning.

- **Suggestion**: Either:
  1. Remove the duplicate constraint recreation at lines 310-313, OR
  2. Add `DROP CONSTRAINT IF EXISTS chk_events_severity` before the ADD CONSTRAINT at line 310

---

### Major Issues

#### Issue 4: Partitioned table swap causes downtime (contradicts zero-downtime claim)
- **Location**: `0011_partition_audit_logs.py:88-89`, `0014_partition_security_events.py:125-126`
- **Severity**: Major
- **Category**: Production Deployment Risk
- **Description**: Both partitioning migrations use a DROP+RENAME table swap pattern:
  ```sql
  DROP TABLE audit_logs;
  ALTER TABLE audit_logs_partitioned RENAME TO audit_logs;
  ```
  `DROP TABLE` acquires an **ACCESS EXCLUSIVE lock** on the old table, and the RENAME acquires ACCESS EXCLUSIVE on the new table. During this window, ALL queries to these tables are blocked. For large tables with active traffic, this is NOT zero-downtime.

  The schema design doc (`schema_changes_aaa.md`) states "ダウンタイム: なし" for 0013 and "中" for 0014, but does not adequately warn about the lock duration during the DROP+RENAME swap for either migration.

- **Suggestion**: Document explicitly that these migrations require a maintenance window. Consider using `pg_repack` or online schema change tools for production environments with large tables. Add a comment at the top of each migration with estimated lock duration.

#### Issue 5: Hardcoded database credentials in alembic.ini
- **Location**: `alembic.ini:4`
- **Severity**: Major
- **Category**: Security
- **Description**: The file contains `postgresql+asyncpg://postgres:password@localhost:5432/cscv2025` with plaintext credentials. If this file is committed to version control, database credentials are exposed.

- **Suggestion**: Use environment variable substitution: `postgresql+asyncpg://%(user)s:%(password)s@%(host)s:%(port)s/%(dbname)s` with values loaded from `.env` or environment variables. Add `alembic.ini` to `.gitignore` or use a template file pattern.

#### Issue 6: Composite PK on partitioned tables breaks application assumptions
- **Location**: `0011_partition_audit_logs.py:39`, `0014_partition_security_events.py:38`
- **Severity**: Major
- **Category**: Bug / Application Compatibility
- **Description**: Both partitioned tables use `PRIMARY KEY (id, created_at)`. The SQLAlchemy models define `id` as the sole PK. This means:
  - `AuditLog.__table__.primary_key` in SQLAlchemy contains only `id`
  - Application code that constructs `WHERE id = :id` queries (without `created_at`) will return ambiguous results or fail
  - ORM operations like `session.query(AuditLog).get(uuid_value)` will fail because the DB expects a composite key
  - Any external tool or direct SQL query assuming single-column PK will break

  DD13 acknowledges this drift but marks it as "tolerated" without documenting the operational impact.

- **Suggestion**: If this drift is intentional, add explicit documentation of affected code paths. Consider using `__mapper_args__` with `primary_key` override in the SQLAlchemy models to reflect the composite key, or use trigger-based UUID generation to maintain single-column PK compatibility.

---

### Minor Issues

#### Issue 7: idx_uploads_hash indexes mostly-NULL column
- **Location**: `0009_add_indexes.py:25`
- **Severity**: Minor
- **Category**: Performance
- **Description**: `file_hash_sha256` is nullable and likely NULL for most rows. A standard B-tree index on a mostly-NULL column wastes storage and provides minimal query benefit.

- **Suggestion**: Use a partial index: `CREATE INDEX idx_uploads_hash ON file_uploads (file_hash_sha256) WHERE file_hash_sha256 IS NOT NULL`

#### Issue 8: 0015 drops CHECK constraint without NOT VALID pattern
- **Location**: `0015_fix_pipeline_runs_status.py:27`
- **Severity**: Minor
- **Category**: Maintainability
- **Description**: Migration 0015 drops and recreates the `chk_runs_status` constraint. The recreation uses `NOT VALID` + `VALIDATE` (good), but the initial drop followed by an unconditional UPDATE means there's a brief window where no constraint guards the column. If concurrent writes occur during migration, invalid values could be inserted between the DROP and UPDATE.

  This is low risk for Alembic (which serializes migrations), but worth noting for production deployments.

- **Suggestion**: Acceptable as-is for Alembic's single-writer model. If deploying with parallel writers, add a temporary constraint allowing both old and new values during the transition.

#### Issue 9: schema_changes_aaa.md is stale
- **Location**: `docs/03_dba/schema_changes_aaa.md:11`
- **Severity**: Minor
- **Category**: Completeness
- **Description**: The document states "Alembic (14ステップ、リニア)" but there are now 15 migrations. The table listing and migration plan sections don't include 0015 (pipeline_runs status standardization).

- **Suggestion**: Update to reflect 15 migrations and add 0015 to the migration plan table.

#### Issue 10: 0010 CHECK constraints not recreated in 0014 downgrade
- **Location**: `0014_partition_security_events.py` (downgrade)
- **Severity**: Minor
- **Category**: Completeness
- **Description**: The 0014 downgrade recreates `chk_events_severity` (which was added in 0010 and re-added in 0014 Step 8), but does not recreate other 0010 constraints that were on the original security_events table before partitioning. Since the partitioned table only re-creates `chk_events_severity`, constraints like those from 0013 (`chk_extract_*`) on other tables are unaffected, but the security_events-specific constraints from 0010 that were implicitly dropped during the table swap should be verified.

  (After review: 0010 only added `chk_events_severity` to security_events, so this is actually fine. The other 0010 constraints are on different tables.)

- **Suggestion**: No action needed — confirmed that `chk_events_severity` is the only 0010 constraint on security_events.

---

### Positive Highlights

1. **NOT VALID + VALIDATE pattern** (0010, 0013, 0015): Excellent zero-downtime approach for CHECK constraints. Adds constraints without scanning existing data, then validates separately.

2. **Dynamic partition date generation** (0011, 0014): Partition creation uses `current_date` rather than hardcoded dates, making migrations reproducible across environments.

3. **Comprehensive downgrade paths** (all migrations): Every migration has a symmetric downgrade, including complex partition teardowns with data preservation.

4. **Partial index for unresolved events** (0013): `idx_events_unresolved` is a well-designed partial index that significantly reduces storage and improves dashboard query performance.

5. **pg_cron automation** (0011, 0014): Automated partition creation and archival reduces operational burden. The quarter-based strategy for security_events is appropriate for the expected data volume.

6. **Migration 0015 data migration safety**: Drops constraint first, updates data, then adds new constraint — correct ordering that prevents constraint violations during the transition.

7. **Index naming conventions**: Consistent prefix scheme (`idx_` for composite/business indexes, `ix_` for FK/single-column indexes) improves discoverability.

---

### Migration Chain Verification

```
0001_initial_schema (down_revision: None)
  → 0002_add_file_integrity
    → 0003_add_rate_limiting
      → 0004_add_scan_results
        → 0005_add_audit_tracing
          → 0006_add_security_resolution
            → 0007_add_user_security_fields
              → 0008_add_api_keys
                → 0009_add_indexes
                  → 0010_add_constraints
                    → 0011_partition_audit_logs
                      → 0012_add_pipeline_executions
                        → 0013_add_constraints_and_indexes
                          → 0014_partition_security_events
                            → 0015_fix_pipeline_runs_status (HEAD)
```

Chain is **linear, contiguous, and valid**. No gaps, no circular dependencies.

### Upgrade/Downgrade Symmetry Check

| Migration | Symmetric? | Notes |
|-----------|-----------|-------|
| 0001-0010 | ✅ Yes | All operations reversed in correct order |
| 0011 | ✅ Yes | PK restored to single-column, FK and indexes recreated |
| 0012-0013 | ✅ Yes | All constraints and indexes dropped in reverse order |
| 0014 | ❌ **No** | Duplicate `chk_events_severity` constraint on downgrade (Critical Issue 3) |
| 0015 | ✅ Yes | Data reversed, original constraint restored |

### FK ondelete Behavior Summary

| FK | OnDelete | Assessment |
|----|----------|-----------|
| file_uploads.user_id → users | CASCADE | ✅ Correct — deleting user removes their uploads |
| audit_logs.user_id → users | SET NULL | ✅ Correct — preserves audit trail |
| extraction_events.upload_id → file_uploads | CASCADE | ✅ Correct — events tied to upload lifecycle |
| security_events.upload_id → file_uploads | CASCADE | ✅ Correct |
| security_events.resolved_by → users | SET NULL | ✅ Correct — preserves resolution history |
| file_scan_results.upload_id → file_uploads | CASCADE | ✅ Correct |
| pipeline_runs.stage_id → pipeline_stages | CASCADE | ✅ Correct |
| rate_limit_events.user_id → users | CASCADE | ✅ Correct |
| api_keys.user_id → users | CASCADE | ✅ Correct |
| pipeline_execution_steps.execution_id → pipeline_executions | CASCADE | ✅ Correct |

All FK behaviors are appropriate for the data model.
