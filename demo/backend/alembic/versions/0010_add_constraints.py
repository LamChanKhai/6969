"""
Revision: 0010_add_constraints
Description: CHECK 制約を追加（NOT VALID + VALIDATE パターンでゼロダウンタイム対応）
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0010_add_constraints'
down_revision: Union[str, None] = '0009_add_indexes'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # CHECK constraints — added as NOT VALID first (no lock on existing data),
    # then validated separately. This enables zero-downtime deployment.

    # file_uploads
    op.execute("ALTER TABLE file_uploads ADD CONSTRAINT chk_file_size CHECK (file_size >= 0) NOT VALID")
    op.execute("ALTER TABLE file_uploads ADD CONSTRAINT chk_scan_status CHECK (security_scan_status IN ('pending', 'passed', 'failed', 'blocked', 'scanning')) NOT VALID")
    op.execute("ALTER TABLE file_uploads ADD CONSTRAINT chk_extraction_status CHECK (extraction_status IN ('pending', 'success', 'failed', 'extracting')) NOT VALID")

    # users
    op.execute("ALTER TABLE users ADD CONSTRAINT chk_users_role CHECK (role IN ('admin', 'operator', 'viewer')) NOT VALID")

    # security_events
    op.execute("ALTER TABLE security_events ADD CONSTRAINT chk_events_severity CHECK (severity IN ('info', 'warning', 'high', 'critical')) NOT VALID")

    # pipeline_runs
    op.execute("ALTER TABLE pipeline_runs ADD CONSTRAINT chk_runs_status CHECK (status IN ('running', 'success', 'failed', 'cancelled')) NOT VALID")
    op.execute("ALTER TABLE pipeline_runs ADD CONSTRAINT chk_runs_duration CHECK (duration_seconds IS NULL OR duration_seconds >= 0) NOT VALID")

    # rate_limit_events
    op.execute("ALTER TABLE rate_limit_events ADD CONSTRAINT chk_rate_action CHECK (action_taken IN ('logged', 'blocked', 'temporary_ban')) NOT VALID")

    # file_scan_results
    op.execute("ALTER TABLE file_scan_results ADD CONSTRAINT chk_scan_status_fsr CHECK (scan_status IN ('pending', 'running', 'completed', 'failed')) NOT VALID")
    op.execute("ALTER TABLE file_scan_results ADD CONSTRAINT chk_scan_threats CHECK (threats_found >= 0) NOT VALID")

    # Validate all constraints (acquires lock but only briefly)
    op.execute("ALTER TABLE file_uploads VALIDATE CONSTRAINT chk_file_size")
    op.execute("ALTER TABLE file_uploads VALIDATE CONSTRAINT chk_scan_status")
    op.execute("ALTER TABLE file_uploads VALIDATE CONSTRAINT chk_extraction_status")
    op.execute("ALTER TABLE users VALIDATE CONSTRAINT chk_users_role")
    op.execute("ALTER TABLE security_events VALIDATE CONSTRAINT chk_events_severity")
    op.execute("ALTER TABLE pipeline_runs VALIDATE CONSTRAINT chk_runs_status")
    op.execute("ALTER TABLE pipeline_runs VALIDATE CONSTRAINT chk_runs_duration")
    op.execute("ALTER TABLE rate_limit_events VALIDATE CONSTRAINT chk_rate_action")
    op.execute("ALTER TABLE file_scan_results VALIDATE CONSTRAINT chk_scan_status_fsr")
    op.execute("ALTER TABLE file_scan_results VALIDATE CONSTRAINT chk_scan_threats")


def downgrade() -> None:
    # Drop CHECK constraints
    op.drop_constraint('chk_scan_threats', 'file_scan_results', type_='check')
    op.drop_constraint('chk_scan_status_fsr', 'file_scan_results', type_='check')
    op.drop_constraint('chk_rate_action', 'rate_limit_events', type_='check')
    op.drop_constraint('chk_runs_duration', 'pipeline_runs', type_='check')
    op.drop_constraint('chk_runs_status', 'pipeline_runs', type_='check')
    op.drop_constraint('chk_events_severity', 'security_events', type_='check')
    op.drop_constraint('chk_users_role', 'users', type_='check')
    op.drop_constraint('chk_extraction_status', 'file_uploads', type_='check')
    op.drop_constraint('chk_scan_status', 'file_uploads', type_='check')
    op.drop_constraint('chk_file_size', 'file_uploads', type_='check')
