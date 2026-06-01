"""
Revision: 0012_add_pipeline_executions
Description: パイプライン実行追跡テーブルを追加
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = '0012_add_pipeline_executions'
down_revision: Union[str, None] = '0011_partition_audit_logs'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'pipeline_executions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('total_steps', sa.Integer(), nullable=False),
        sa.Column('current_step', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('status', sa.String(20), nullable=False, server_default='running'),
        sa.Column('step_logs', sa.Text(), nullable=False, server_default=''),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('idx_pipeline_executions_status', 'pipeline_executions', ['status'])

    op.create_table(
        'pipeline_execution_steps',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('execution_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('pipeline_executions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('step_number', sa.Integer(), nullable=False),
        sa.Column('step_name', sa.String(200), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('logs', sa.Text(), nullable=False, server_default=''),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('duration_seconds', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_pipeline_execution_steps_execution_id', 'pipeline_execution_steps', ['execution_id'])
    op.create_index('idx_pipeline_exec_steps_status', 'pipeline_execution_steps', ['execution_id', 'status'])


def downgrade() -> None:
    op.drop_index('idx_pipeline_exec_steps_status', table_name='pipeline_execution_steps')
    op.drop_index('ix_pipeline_execution_steps_execution_id', table_name='pipeline_execution_steps')
    op.drop_table('pipeline_execution_steps')
    op.drop_index('idx_pipeline_executions_status', table_name='pipeline_executions')
    op.drop_table('pipeline_executions')
