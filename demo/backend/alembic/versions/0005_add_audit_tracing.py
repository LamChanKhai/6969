"""
Revision: 0005_add_audit_tracing
Description: audit_logs に分散トレーシングカラムを追加
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0005_add_audit_tracing'
down_revision: Union[str, None] = '0004_add_scan_results'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('audit_logs', sa.Column('session_id', sa.String(100), nullable=True))
    op.add_column('audit_logs', sa.Column('request_id', sa.String(100), nullable=True))


def downgrade() -> None:
    op.drop_column('audit_logs', 'request_id')
    op.drop_column('audit_logs', 'session_id')
