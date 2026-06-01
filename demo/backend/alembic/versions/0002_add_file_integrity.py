"""
Revision: 0002_add_file_integrity
Description: file_uploads にファイル完全性検証カラムを追加
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0002_add_file_integrity'
down_revision: Union[str, None] = '0001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('file_uploads', sa.Column('file_hash_sha256', sa.String(64), nullable=True))
    op.add_column('file_uploads', sa.Column('archived', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('file_uploads', sa.Column('archived_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('file_uploads', 'archived_at')
    op.drop_column('file_uploads', 'archived')
    op.drop_column('file_uploads', 'file_hash_sha256')
