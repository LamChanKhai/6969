# Migration Review — Project AAA (Updated)

**Review Date**: 2026-05-30
**Reviewer**: Senior Backend Reviewer
**Scope**: 14 Alembic migrations (`0001` → `0014`), 12 ORM models, migration test suite
**Previous Review**: `docs/review_migration_review.md` (covered 0001–0011 only)

**Migration Stack**: PostgreSQL, SQLAlchemy 2.0 async ORM, Alembic
**Migration Chain**: Linear, 14 steps, no branches

---

## Review Summary

**Type**: Code Review — Database Migrations
**Files Reviewed**: 14 migration files + 1 model file + 1 test file + 1 env.py + 1 alembic.ini = **17 files**
**Overall Assessment**: **Needs Changes** — 5 critical issues, 5 major issues, 3 suggestions

**Note**: The previous review (covering 0001–0011) identified 4 critical issues. Issues #1 (FK ondelete in 0010), #2 (FK recreation locks in 0010), and #3 (pg_cron on non-partitioned tables in 0011) have been **resolved** in the current codebase. Issue #4 (`create_type=False` in 0001) was a **false positive** — the enum is created explicitly on line 21, and `create_type=False` correctly prevents a duplicate. This review focuses on the current state of all 14 migrations.

---

### Critical Issues

#### Issue 1: Test suite is outdated — only covers up to 0011, but head is now 0014
- **Location**: `tests/test_migrations.py:380-383`, `:500-545`, `:580-586`
- **Severity**: Critical
- **Category**: Testing / Deployment Reliability
- **Description**: The test suite expects head revision to be `0011_partition_audit_logs` (line 383), but the actual head is now `0014_partition_security_events`. Three entire migrations (0012, 0013, 0014) are completely untested:
  - `test_03_upgrade_to_head` asserts `version == "0011_partition_audit_logs"` — will fail immediately
  - `test_08_step_by_step_downgrade` and `test_09_step_by_step_upgrade` iterate only through 0001–0011
  - `test_12_history_check` only verifies 11 revisions exist
  - `EXPECTED_CHECKS` is missing `chk_exec_status`, `chk_exec_steps_range`, `chk_exec_step_status`, `chk_extract_status`, `chk_extract_event_type`, `chk_stages_name_not_empty`
  - `EXPECTED_FKS` expects renamed FK names (`fk_uploads_user`, etc.) that are never created by the current migrations — only `fk_audit_user` (0011) and `fk_security_events_upload` / `fk_security_events_resolved_by` (0014) use explicit names. The remaining 6 FKs have auto-generated names.
- **Suggestion**: Update all test constants and revision references to cover 0012–0014. Fix `EXPECTED_FKS` to match actual FK constraint names in the database. Add the new CHECK constraints to `EXPECTED_CHECKS`.

#### Issue 2: 0011 and 0014 downgrade — `LIKE ... INCLUDING ALL` copies indexes, then downgrade recreates them, causing duplicate index errors
- **Location**: `0011_partition_audit_logs.py:165-182`, `0014_partition_security_events.py:203-240`
- **Severity**: Critical
- **Category**: Data Corruption Risk / Rollback Failure
- **Description**: Both partitioning migrations use the same downgrade pattern:
  ```python
  op.execute("CREATE TABLE audit_logs_temp (LIKE audit_logs INCLUDING ALL)")
  ```
  `INCLUDING ALL` copies indexes from the partitioned parent table. The partitioned parent has indexes created during upgrade (e.g., `ix_audit_logs_created_at` in 0011 Step 5). Then the downgrade explicitly recreates these same indexes:
  ```python
  op.execute("CREATE INDEX ix_audit_logs_created_at ON audit_logs (created_at)")
  ```
  This produces `duplicate key value violates unique constraint` or `relation already exists` errors, causing the downgrade to fail partway through — leaving the database in a broken state with orphaned partition tables and a half-migrated `audit_logs_temp`.

  The same pattern exists in 0014, where 7 indexes are copied by `INCLUDING ALL` and then 7 more are explicitly created.

- **Suggestion**: Either:
  - Use `LIKE ... INCLUDING DEFAULTS INCLUDING CONSTRAINTS` (without `ALL` / `INDEXES`) to avoid copying indexes, then create them explicitly
  - Or drop the copied indexes before creating the explicit ones:
    ```python
    op.execute("CREATE TABLE audit_logs_temp (LIKE audit_logs INCLUDING ALL)")
    op.execute("DROP INDEX IF EXISTS ix_audit_logs_created_at ON audit_logs_temp")
    # ... then create indexes explicitly
    ```

#### Issue 3: 0011 and 0014 partition dates are hardcoded to 2025
- **Location**: `0011_partition_audit_logs.py:45-55`, `0014_partition_security_events.py:43-59`
- **Severity**: Critical
- **Category**: Data Corruption Risk
- **Description**: Partition ranges are hardcoded to 2025 dates:
  - 0011: `audit_logs_2025_04`, `audit_logs_2025_05`, `audit_logs_2025_06`
  - 0014: `security_events_2025_q1` through `q4`

  Today's date is **2026-05-30**. Running these migrations now will:
  - Create partitions for months/quarters that have already passed
  - New data inserted at `NOW()` will fall outside all partition ranges
  - INSERT will fail with "no partition of table 'audit_logs' found for row" — **silent data loss** from the application's perspective (the error bubbles up as a database exception)

  The pg_cron jobs create FUTURE partitions correctly (they use `current_date`), but the initial partition set is stale.

- **Suggestion**: Use dynamic date calculation in the migration:
  ```python
  op.execute("""
      DO $$
      DECLARE
          current_month_start DATE := date_trunc('month', current_date);
          last_month_start DATE := current_month_start - interval '1 month';
          next_month_start DATE := current_month_start + interval '1 month';
      BEGIN
          EXECUTE format('CREATE TABLE %I PARTITION OF audit_logs_partitioned FOR VALUES FROM (%L) TO (%L)',
              'audit_logs_' || to_char(last_month_start, 'YYYY_MM'), last_month_start, current_month_start);
          -- ... current and next month
      END $$
  """)
  ```

#### Issue 4: 0014 pg_cron archive job detaches ALL partitions unconditionally — `cutoff_date` is never used
- **Location**: `0014_partition_security_events.py:155-182`
- **Severity**: Critical
- **Category**: Data Loss Risk
- **Description**: The archive cron job declares `cutoff_date` but never references it in the LOOP:
  ```python
  cutoff_date DATE := current_date - interval '24 months';  -- declared but unused
  FOR partition_name IN ... LOOP
      -- No date check! Detaches EVERY matching partition every quarter
      EXECUTE format('ALTER TABLE security_events DETACH PARTITION %I', partition_name);
  ```
  Compare with 0011's archive job, which correctly filters:
  ```python
  IF to_date(substring(partition_name from 13), 'YYYY_MM') < cutoff_date THEN
  ```
  The 0014 version will detach ALL partitions (including current/recent ones) every quarter, causing INSERT failures for data that no longer has a matching partition.

- **Suggestion**: Add the missing date filter:
  ```python
  IF to_date(substring(partition_name from 19), 'YYYY') < EXTRACT(YEAR FROM cutoff_date)
     OR (to_date(substring(partition_name from 19), 'YYYY') = EXTRACT(YEAR FROM cutoff_date)
         AND ... ) THEN
  ```
  Or simpler: parse the quarter from the partition name and compare against `cutoff_date`.

#### Issue 5: 0011 and 0014 downgrade do not restore original single-column PK — `created_at` remains in composite PK
- **Location**: `0011_partition_audit_logs.py:165`, `0014_partition_security_events.py:203`
- **Severity**: Critical
- **Category**: Schema Inconsistency
- **Description**: The original `audit_logs` table (0001) has `PRIMARY KEY (id)`. The partitioned version has `PRIMARY KEY (id, created_at)` (required for partitioning). The downgrade uses `LIKE audit_logs INCLUDING ALL`, which copies the composite PK from the partitioned parent. The restored table therefore has `PRIMARY KEY (id, created_at)` instead of the original `PRIMARY KEY (id)`.

  This breaks:
  - Application code that assumes single-column PK (e.g., `UPDATE audit_logs SET ... WHERE id = ?`)
  - ORM behavior — the model defines `created_at` as part of the composite PK at HEAD, but this wouldn't match the pre-partitioning schema
  - Any external tools or queries relying on `id` as the sole PK

  The same issue exists in 0014 for `security_events`.

- **Suggestion**: After renaming `audit_logs_temp` to `audit_logs`, explicitly reset the PK:
  ```python
  op.execute("ALTER TABLE audit_logs DROP CONSTRAINT audit_logs_pkey")
  op.execute("ALTER TABLE audit_logs ADD PRIMARY KEY (id)")
  ```

---

### Major Issues

#### Warning 1: 0011 Step 7 — tautological CHECK constraint added, validated, then immediately dropped
- **Location**: `0011_partition_audit_logs.py:81-87`
- **Severity**: Major
- **Category**: Code Quality / Maintainability
- **Description**:
  ```python
  op.execute("ALTER TABLE audit_logs ADD CONSTRAINT chk_audit_logs_valid CHECK (true) NOT VALID")
  op.execute("ALTER TABLE audit_logs VALIDATE CONSTRAINT chk_audit_logs_valid")
  op.execute("ALTER TABLE audit_logs DROP CONSTRAINT chk_audit_logs_valid")
  ```
  `CHECK (true)` is always satisfied. Adding, validating, and immediately dropping it serves no purpose. This wastes migration time (validation scans all rows) and confuses reviewers.

- **Suggestion**: Remove Steps 7 entirely. If this was a placeholder for real constraints, either add the actual constraints or delete the placeholder.

#### Warning 2: 0009 docstring claims "CONCURRENTLY 対応" but uses blocking `op.create_index()`
- **Location**: `0009_add_indexes.py:3` (docstring) vs `:17-42` (implementation)
- **Severity**: Major
- **Category**: Zero-Downtime Deployment
- **Description**: The docstring says "パフォーマンス最適化用の複合インデックスを追加（CONCURRENTLY 対応）" (composite indexes for performance optimization, CONCURRENTLY compatible), but all 13 indexes are created with `op.create_index()`, which uses regular `CREATE INDEX` (exclusive lock, blocks writes). On large tables (`audit_logs`, `security_events`), this blocks writes for the duration of index construction.

- **Suggestion**: Either:
  - Use raw SQL with `CREATE INDEX CONCURRENTLY` (requires `transactional_ddl = False` in the migration)
  - Or update the docstring to reflect that these are standard blocking indexes requiring a maintenance window

#### Warning 3: `pipeline_runs.status` vs `pipeline_executions.status` use different value sets
- **Location**: `0010_add_constraints.py:34` (`chk_runs_status`) vs `0013_add_constraints_and_indexes.py:55` (`chk_exec_status`)
- **Severity**: Major
- **Category**: Data Integrity / Consistency
- **Description**: Two different tables tracking pipeline execution use incompatible status values:
  - `pipeline_runs.status`: `'running'`, `'success'`, `'failed'`, `'cancelled'`
  - `pipeline_executions.status`: `'running'`, `'completed'`, `'failed'`, `'cancelled'`

  `'success'` vs `'completed'` will cause confusion in dashboards, reports, and API responses. Code that normalizes statuses across both tables will need special-case handling.

- **Suggestion**: Standardize on one term. `'completed'` is more conventional. Update `chk_runs_status` to use `'completed'` instead of `'success'` (requires a data migration to update existing rows).

#### Warning 4: Model defines `AuditLog.created_at` and `SecurityEvent.created_at` as composite PK, but initial migration (0001) creates single-column PK
- **Location**: `app/models/models.py:122-124` (AuditLog), `:178-180` (SecurityEvent) vs `0001_initial_schema.py:58-68`, `:87-96`
- **Severity**: Major
- **Category**: Model-Migration Drift
- **Description**: The ORM model declares `created_at` as `primary_key=True` for both `AuditLog` and `SecurityEvent`, creating composite PKs `(id, created_at)`. However, migration 0001 creates these tables with `id` as the sole primary key. The composite PK is only introduced by migrations 0011 and 0014 (for partitioning).

  This means the model is only accurate at HEAD revision. At any revision before 0011/0014, the model and schema are inconsistent. While this is a practical reality (models reflect the latest schema), it means:
  - `alembic autogenerate` will detect this drift and propose unwanted changes
  - Running the application against a database at an intermediate revision will cause ORM errors

- **Suggestion**: Document this drift explicitly. Consider using `__table_args__` with conditional PK definition, or accept that the model reflects HEAD-only (common practice, but should be documented).

#### Warning 5: 0013 UNIQUE constraint on `pipeline_stages.stage_name` — `CREATE UNIQUE INDEX` requires exclusive lock
- **Location**: `0013_add_constraints_and_indexes.py:34-38`
- **Severity**: Major
- **Category**: Zero-Downtime Deployment
- **Description**: `op.create_unique_constraint()` acquires an `ACCESS EXCLUSIVE` lock on `pipeline_stages`. The docstring acknowledges this ("pipeline_stages はほぼ静的データのため影響最小"), which is a reasonable assessment for a small, rarely-modified table. However, if `pipeline_stages` has active writes during deployment (e.g., admin configuring pipeline stages), this will block them.

- **Suggestion**: Acceptable as-is for a small static table, but document the expected lock duration (< 1 second for < 100 rows). Consider adding a comment in the migration with the maintenance window recommendation.

---

### Suggestions

#### Suggestion 1: Add `PipelineExecution` ↔ `PipelineExecutionStep` relationship to the model
- **Location**: `app/models/models.py:348-372` (PipelineExecution), `:374-402` (PipelineExecutionStep)
- **Category**: Code Quality
- **Description**: `PipelineExecutionStep` has `execution_id` FK to `pipeline_executions.id`, but neither model defines a `relationship()` to link them. `PipelineExecution` lacks `steps: Mapped[list["PipelineExecutionStep"]]`, and `PipelineExecutionStep` lacks `execution: Mapped["PipelineExecution"]`.

#### Suggestion 2: 0014 pg_cron partition creation — `q_num` logic runs on the month the cron fires, not the target quarter
- **Location**: `0014_partition_security_events.py:109-152`
- **Category**: Correctness
- **Description**: The cron fires on the 1st of every quarter month (`'0 0 1 */3 *'`). The `q_num` calculation uses `current_date` to determine the current quarter, then creates the NEXT quarter's partition. This is correct in principle, but the cron schedule `*/3` means it fires on months 1, 4, 7, 10. When it fires on January 1st, `q_num = 1`, so it creates Q2. When it fires on April 1st, `q_num = 2`, so it creates Q3. This is correct. No issue — just noting for reviewer awareness.

#### Suggestion 3: Add `pipeline_executions` and `pipeline_execution_steps` data to `insert_sample_data` / `verify_sample_data` in tests
- **Location**: `tests/test_migrations.py:200-306`
- **Category**: Testing
- **Description**: The sample data insertion and verification functions don't cover `pipeline_executions` or `pipeline_execution_steps` tables (added in 0012). Data preservation through downgrade/upgrade cycles is untested for these tables.

---

### Positive Highlights

1. **NOT VALID + VALIDATE pattern**: Migrations 0010, 0013 correctly use the two-phase CHECK constraint approach for zero-downtime deployment. This is best practice for PostgreSQL.
2. **Comprehensive CHECK constraints**: 16 CHECK constraints across 7 tables enforce data integrity at the database level.
3. **Partitioning strategy is sound**: The table-replacement approach (create new → copy data → swap → recreate indexes/FKs) is the correct way to convert a non-partitioned table to a partitioned one.
4. **pg_cron automation**: Automated partition creation and archival reduces operational burden.
5. **Partial index for unresolved events** (0013): `idx_events_unresolved` with `WHERE (is_resolved = false)` is an excellent optimization for dashboard queries.
6. **Symmetric downgrades for 0012 and 0013**: Clean, complete rollback paths.
7. **`resolved_by` index added** (0009): Addresses the FK lookup performance concern from the previous review.
8. **Unique constraint on `pipeline_stages.stage_name`** (0013): Prevents ambiguous stage names.

---

## Zero-Downtime Deployment Safety Assessment

| Migration | Safe for Zero-Downtime? | Risk |
|---|---|---|
| 0001 | ✅ Yes | Creates new tables, no existing data |
| 0002 | ✅ Yes | Adds nullable columns with defaults |
| 0003 | ✅ Yes | Creates new table |
| 0004 | ✅ Yes | Creates new table |
| 0005 | ✅ Yes | Adds nullable columns |
| 0006 | ✅ Yes | Adds nullable FK with SET NULL |
| 0007 | ✅ Yes | Adds columns with defaults |
| 0008 | ✅ Yes | Creates new table |
| 0009 | ❌ No | `CREATE INDEX` blocks writes on large tables |
| 0010 | ⚠️ Partial | NOT VALID is safe; VALIDATE acquires SHARE ROW EXCLUSIVE lock |
| 0011 | ❌ No | Table replacement requires exclusive locks, DROP TABLE blocks all access |
| 0012 | ✅ Yes | Creates new tables |
| 0013 | ⚠️ Partial | UNIQUE constraint requires exclusive lock; CHECK NOT VALID is safe, VALIDATE locks briefly |
| 0014 | ❌ No | Same table-replacement risks as 0011 |

**Verdict**: Migrations 0009, 0011, 0013, and 0014 require a maintenance window. Migrations 0010 is mostly safe but VALIDATE steps should be timed during low-traffic periods.

---

## Upgrade/Downgrade Symmetry Analysis

| Migration | Symmetric? | Notes |
|---|---|---|
| 0001 | ✅ Yes | All tables, indexes, enum type properly reversed |
| 0002 | ✅ Yes | Column add/drop in reverse order |
| 0003 | ✅ Yes | Table and indexes reversed |
| 0004 | ✅ Yes | Table and indexes reversed |
| 0005 | ✅ Yes | Column add/drop in reverse order |
| 0006 | ✅ Yes | Column add/drop in reverse order |
| 0007 | ✅ Yes | Column add/drop in reverse order |
| 0008 | ✅ Yes | Table and index reversed |
| 0009 | ✅ Yes | All 13 indexes dropped in reverse order |
| 0010 | ✅ Yes | All 10 CHECK constraints dropped |
| 0011 | ❌ No | Downgrade fails with duplicate index errors (Critical Issue 2). Composite PK not restored to single-column (Critical Issue 5) |
| 0012 | ✅ Yes | Both tables and all indexes dropped |
| 0013 | ✅ Yes | UNIQUE, CHECK constraints, and indexes all dropped |
| 0014 | ❌ No | Same downgrade issues as 0011 (Critical Issues 2 and 5) |

---

## Previous Review Resolution Status

| Previous Issue | Status | Notes |
|---|---|---|
| #1: 0010 FK ondelete lost in downgrade | ✅ Resolved | 0010 no longer recreates FKs — CHECK constraints only |
| #2: 0010 FK recreation locks | ✅ Resolved | FK recreation block removed entirely |
| #3: 0011 pg_cron on non-partitioned tables | ✅ Resolved | Uses proper table-replacement approach now |
| #4: 0001 `create_type=False` failure | ✅ False Positive | Enum created explicitly on line 21; `create_type=False` prevents duplicate |
| W1: Redundant indexes (0001 vs 0009) | ⚠️ Partial | `idx_audit_time_range` removed, but `ix_audit_logs_user_id` still overlaps with `idx_audit_user_action` |
| W2: 0009 blocking index creation | ❌ Open | Docstring updated to claim CONCURRENTLY but implementation unchanged |
| W3: Missing `resolved_by` index | ✅ Resolved | Added in 0009 as `ix_security_events_resolved_by` |
| W4: `upload_id` FK index | ✅ Resolved | `ix_scan_upload_status` composite index covers FK check |
| W5: CHECK constraint locking | ✅ Resolved | Uses NOT VALID + VALIDATE pattern |
| S1: Missing `upload_id` single-column index | ⚠️ Open | Still relies on composite index |
| S2: `pipeline_stages.stage_name` uniqueness | ✅ Resolved | Added in 0013 |
| S3: Partial downgrade/upgrade data test | ❌ Open | Test suite still only covers full downgrade |
