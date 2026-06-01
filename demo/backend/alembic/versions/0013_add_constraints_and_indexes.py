"""
Revision: 0013_add_constraints_and_indexes
Description: CHECK制約追加、UNIQUE制約、部分インデックスを追加

対象:
- pipeline_stages.stage_name に UNIQUE 制約を追加
- pipeline_executions に status CHECK 制約を追加
- pipeline_execution_steps に status CHECK 制約を追加
- extraction_events に status, event_type CHECK 制約を追加
- security_events に未解決イベント用の部分インデックスを追加
- pipeline_executions に複合インデックスを追加

ゼロダウンタイム対応:
- CHECK 制約は NOT VALID + VALIDATE パターンを使用
- UNIQUE 制約は排他ロックが必要（pipeline_stages はほぼ静的データのため影響最小）
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0013_add_constraints_and_indexes'
down_revision: Union[str, None] = '0012_add_pipeline_executions'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- UNIQUE constraint on pipeline_stages.stage_name ---
    # pipeline_stages is a small, mostly static table. The exclusive lock
    # required for CREATE UNIQUE INDEX is acceptable here.
    op.create_unique_constraint(
        'uq_pipeline_stages_stage_name',
        'pipeline_stages',
        ['stage_name']
    )

    # --- CHECK constraint: pipeline_stages.stage_name not empty ---
    op.execute(
        "ALTER TABLE pipeline_stages "
        "ADD CONSTRAINT chk_stages_name_not_empty "
        "CHECK (stage_name <> '') NOT VALID"
    )
    op.execute(
        "ALTER TABLE pipeline_stages "
        "VALIDATE CONSTRAINT chk_stages_name_not_empty"
    )

    # --- CHECK constraints: pipeline_executions ---
    op.execute(
        "ALTER TABLE pipeline_executions "
        "ADD CONSTRAINT chk_exec_status "
        "CHECK (status IN ('running', 'completed', 'failed', 'cancelled')) NOT VALID"
    )
    op.execute(
        "ALTER TABLE pipeline_executions "
        "VALIDATE CONSTRAINT chk_exec_status"
    )

    op.execute(
        "ALTER TABLE pipeline_executions "
        "ADD CONSTRAINT chk_exec_steps_range "
        "CHECK (current_step >= 0 AND current_step <= total_steps) NOT VALID"
    )
    op.execute(
        "ALTER TABLE pipeline_executions "
        "VALIDATE CONSTRAINT chk_exec_steps_range"
    )

    # --- CHECK constraints: pipeline_execution_steps ---
    op.execute(
        "ALTER TABLE pipeline_execution_steps "
        "ADD CONSTRAINT chk_exec_step_status "
        "CHECK (status IN ('pending', 'running', 'completed', 'failed', 'skipped')) NOT VALID"
    )
    op.execute(
        "ALTER TABLE pipeline_execution_steps "
        "VALIDATE CONSTRAINT chk_exec_step_status"
    )

    # --- CHECK constraints: extraction_events ---
    op.execute(
        "ALTER TABLE extraction_events "
        "ADD CONSTRAINT chk_extract_status "
        "CHECK (status IN ('success', 'failed', 'pending', 'in_progress')) NOT VALID"
    )
    op.execute(
        "ALTER TABLE extraction_events "
        "VALIDATE CONSTRAINT chk_extract_status"
    )

    op.execute(
        "ALTER TABLE extraction_events "
        "ADD CONSTRAINT chk_extract_event_type "
        "CHECK (event_type IN ('file_extracted', 'path_traversal_detected', 'extraction_failed', 'extraction_started')) NOT VALID"
    )
    op.execute(
        "ALTER TABLE extraction_events "
        "VALIDATE CONSTRAINT chk_extract_event_type"
    )

    # --- Partial index: security_events unresolved events ---
    # Dramatically improves dashboard queries that filter is_resolved = false
    # Partial index only stores rows where is_resolved = false, reducing size
    op.execute(
        "CREATE INDEX idx_events_unresolved "
        "ON security_events (created_at DESC) "
        "WHERE (is_resolved = false)"
    )

    # --- Composite index: pipeline_executions ---
    op.create_index(
        'idx_exec_steps_status_time',
        'pipeline_executions',
        ['status', 'created_at'],
        unique=False
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_exec_steps_status_time', table_name='pipeline_executions')
    op.drop_index('idx_events_unresolved', table_name='security_events')

    # Drop CHECK constraints
    op.drop_constraint('chk_extract_event_type', 'extraction_events', type_='check')
    op.drop_constraint('chk_extract_status', 'extraction_events', type_='check')
    op.drop_constraint('chk_exec_step_status', 'pipeline_execution_steps', type_='check')
    op.drop_constraint('chk_exec_steps_range', 'pipeline_executions', type_='check')
    op.drop_constraint('chk_exec_status', 'pipeline_executions', type_='check')
    op.drop_constraint('chk_stages_name_not_empty', 'pipeline_stages', type_='check')

    # Drop UNIQUE constraint
    op.drop_constraint('uq_pipeline_stages_stage_name', 'pipeline_stages', type_='unique')
