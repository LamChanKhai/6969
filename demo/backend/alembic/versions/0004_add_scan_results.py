"""
Revision: 0004_add_scan_results
Description: ファイルスキャン詳細結果テーブルを作成
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = '0004_add_scan_results'
down_revision: Union[str, None] = '0003_add_rate_limiting'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'file_scan_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('upload_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('file_uploads.id', ondelete='CASCADE'), nullable=False),
        sa.Column('scanner_name', sa.String(100), nullable=False),
        sa.Column('scanner_version', sa.String(50), nullable=True),
        sa.Column('scan_type', sa.String(50), nullable=False),
        sa.Column('scan_status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('threats_found', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('scan_details', sa.Text(), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_scan_upload_status', 'file_scan_results', ['upload_id', 'scan_status'])
    op.create_index('ix_scan_type_created', 'file_scan_results', ['scan_type', 'created_at'])


def downgrade() -> None:
    op.drop_index('ix_scan_type_created', table_name='file_scan_results')
    op.drop_index('ix_scan_upload_status', table_name='file_scan_results')
    op.drop_table('file_scan_results')
