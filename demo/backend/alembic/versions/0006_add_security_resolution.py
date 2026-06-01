"""
Revision: 0006_add_security_resolution
Description: security_events にインシデント解決追跡カラムを追加
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = '0006_add_security_resolution'
down_revision: Union[str, None] = '0005_add_audit_tracing'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('security_events', sa.Column('is_resolved', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('security_events', sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('security_events', sa.Column('resolved_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True))


def downgrade() -> None:
    op.drop_column('security_events', 'resolved_by')
    op.drop_column('security_events', 'resolved_at')
    op.drop_column('security_events', 'is_resolved')
