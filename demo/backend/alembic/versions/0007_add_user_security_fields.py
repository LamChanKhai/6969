"""
Revision: 0007_add_user_security_fields
Description: users にセキュリティ関連カラムを追加
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0007_add_user_security_fields'
down_revision: Union[str, None] = '0006_add_security_resolution'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('users', sa.Column('login_attempts', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('users', sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True))
    op.add_column('users', sa.Column('failed_login_attempts', sa.Integer(), nullable=False, server_default='0'))


def downgrade() -> None:
    op.drop_column('users', 'failed_login_attempts')
    op.drop_column('users', 'locked_until')
    op.drop_column('users', 'login_attempts')
    op.drop_column('users', 'last_login_at')
