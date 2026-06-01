"""
Revision: 0003_add_rate_limiting
Description: レートリミット追跡テーブルを作成
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = '0003_add_rate_limiting'
down_revision: Union[str, None] = '0002_add_file_integrity'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'rate_limit_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=False),
        sa.Column('endpoint', sa.String(255), nullable=False),
        sa.Column('request_count', sa.Integer(), nullable=False),
        sa.Column('window_start', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('window_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('action_taken', sa.String(50), nullable=False, server_default='logged'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_rate_limit_ip_time', 'rate_limit_events', ['ip_address', 'created_at'])
    op.create_index('ix_rate_limit_user_time', 'rate_limit_events', ['user_id', 'created_at'])


def downgrade() -> None:
    op.drop_index('ix_rate_limit_user_time', table_name='rate_limit_events')
    op.drop_index('ix_rate_limit_ip_time', table_name='rate_limit_events')
    op.drop_table('rate_limit_events')
