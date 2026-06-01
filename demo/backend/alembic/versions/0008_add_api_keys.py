"""
Revision: 0008_add_api_keys
Description: API キー管理テーブルを作成
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = '0008_add_api_keys'
down_revision: Union[str, None] = '0007_add_user_security_fields'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'api_keys',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('key_hash', sa.String(255), nullable=False, unique=True),
        sa.Column('key_prefix', sa.String(8), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_apikeys_user_active', 'api_keys', ['user_id', 'is_active'])


def downgrade() -> None:
    op.drop_index('ix_apikeys_user_active', table_name='api_keys')
    op.drop_table('api_keys')
