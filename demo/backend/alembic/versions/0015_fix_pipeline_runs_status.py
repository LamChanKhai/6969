"""
Revision: 0015_fix_pipeline_runs_status
Description: pipeline_runs.status の値を 'success' から 'completed' に標準化

pipeline_executions.status との整合性を確保するため、
pipeline_runs.status の 'success' を 'completed' に変更し、
CHECK 制約を更新します。

データマイグレーション:
- 既存の 'success' 値を 'completed' に更新
- CHECK 制約を置き換え
"""

from typing import Sequence, Union

from alembic import op


revision: str = '0015_fix_pipeline_runs_status'
down_revision: Union[str, None] = '0014_partition_security_events'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop existing CHECK constraint
    op.drop_constraint('chk_runs_status', 'pipeline_runs', type_='check')

    # Migrate data: 'success' -> 'completed'
    op.execute("""
        UPDATE pipeline_runs
        SET status = 'completed'
        WHERE status = 'success'
    """)

    # Recreate CHECK constraint with standardized values
    op.execute("""
        ALTER TABLE pipeline_runs
        ADD CONSTRAINT chk_runs_status
        CHECK (status IN ('running', 'completed', 'failed', 'cancelled'))
        NOT VALID
    """)
    op.execute("""
        ALTER TABLE pipeline_runs
        VALIDATE CONSTRAINT chk_runs_status
    """)


def downgrade() -> None:
    # Drop updated CHECK constraint
    op.drop_constraint('chk_runs_status', 'pipeline_runs', type_='check')

    # Revert data: 'completed' -> 'success'
    op.execute("""
        UPDATE pipeline_runs
        SET status = 'success'
        WHERE status = 'completed'
    """)

    # Recreate original CHECK constraint
    op.execute("""
        ALTER TABLE pipeline_runs
        ADD CONSTRAINT chk_runs_status
        CHECK (status IN ('running', 'success', 'failed', 'cancelled'))
        NOT VALID
    """)
    op.execute("""
        ALTER TABLE pipeline_runs
        VALIDATE CONSTRAINT chk_runs_status
    """)
