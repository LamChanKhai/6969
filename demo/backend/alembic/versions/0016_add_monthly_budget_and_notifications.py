"""
Revision: 0016_add_monthly_budget_and_notifications
Description: Add monthly budget tracking and notification system

New tables:
- monthly_budgets: Track per-user monthly usage limits (uploads, storage, API calls)
- notifications: Store user notifications including budget alerts
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0016_add_monthly_budget_and_notifications'
down_revision: Union[str, None] = '0015_fix_pipeline_runs_status'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create monthly_budgets table
    op.create_table(
        'monthly_budgets',
        sa.Column('id', sa.Uuid(), nullable=False, primary_key=True),
        sa.Column('user_id', sa.Uuid(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True, unique=True),
        sa.Column('month', sa.String(7), nullable=False),
        sa.Column('upload_limit', sa.Integer(), nullable=False, server_default='1000'),
        sa.Column('upload_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('storage_limit_bytes', sa.Integer(), nullable=False, server_default=str(50 * 1024 * 1024 * 1024)),
        sa.Column('storage_used_bytes', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('api_call_limit', sa.Integer(), nullable=False, server_default='10000'),
        sa.Column('api_call_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('budget_exceeded', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('notified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Create unique constraint on (user_id, month)
    op.create_unique_constraint('uq_budget_user_month', 'monthly_budgets', ['user_id', 'month'])

    # Create notifications table
    op.create_table(
        'notifications',
        sa.Column('id', sa.Uuid(), nullable=False, primary_key=True),
        sa.Column('user_id', sa.Uuid(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('notification_type', sa.String(50), nullable=False, server_default='info'),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), index=True),
    )

    # Create indexes
    op.create_index('ix_notifications_user_read', 'notifications', ['user_id', 'is_read'])


def downgrade() -> None:
    op.drop_index('ix_notifications_user_read', table_name='notifications')
    op.drop_table('notifications')
    op.drop_constraint('uq_budget_user_month', 'monthly_budgets', type_='unique')
    op.drop_table('monthly_budgets')
