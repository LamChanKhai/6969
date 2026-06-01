# Handoff Note: Reviewer → Backend Developer

**From**: Reviewer
**To**: Backend Developer
**Date**: 2026-05-31
**Status**: Review complete — **3 Critical issues require fixes**

---

## Deliverable

- `docs/04_reviewer/migration_review_aaa.md` — Full migration review (15 migrations, 0001-0015)

---

## Critical Issues (Must Fix Before Production)

### 1. security_events archive cron — wrong substring offsets (`0014:237-238`)
`substring(from 19, 4)` and `substring(from 24)` are off. Partition names like `security_events_2026_q1` are 23 chars. Year starts at position **17**, quarter digit at **23**. Archive job will fail silently every run — storage grows unbounded.

**Fix**: Change to `substring(from 17, 4)` and `substring(from 23)`.

### 2. audit_logs archive cron — wrong substring offset (`0011:151`)
`substring(from 13)` should be `substring(from 12)`. Partition names like `audit_logs_2026_05` have the year starting at position 12. Archive job will fail silently.

**Fix**: Change to `substring(from 12)`.

### 3. security_events downgrade — duplicate constraint error (`0014:273, 310-313`)
`LIKE ... INCLUDING CONSTRAINTS` copies `chk_events_severity` to the temp table. Lines 310-313 then try to add it again → `duplicate constraint name` error. Downgrade from 0014 is broken.

**Fix**: Either remove lines 310-313, or add `DROP CONSTRAINT IF EXISTS chk_events_severity` before the ADD CONSTRAINT.

---

## Summary

| Category | Count |
|----------|-------|
| Critical | 3 (must fix) |
| Major | 3 (should fix) |
| Minor | 4 (can defer) |
| Positive highlights | 7 |

The migration chain is linear and valid. FK ondelete behaviors are all correct. The NOT VALID + VALIDATE pattern for CHECK constraints is excellent. The two substring bugs (Issues 1-2) are the same root cause: off-by-one/partition-name-length miscalculation. The downgrade bug (Issue 3) is a straightforward constraint name collision.

**Recommended action**: Fix the 3 critical issues, then re-run `test_migrations.py` to verify full upgrade → downgrade cycle passes cleanly.

---

## Next Steps for Backend Developer

1. Fix Issues 1-3 in the migration files
2. Re-run migration test suite
3. Proceed to Cloud Expert handoff when all critical issues are resolved
