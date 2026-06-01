"""
Revision: 0001_initial_schema
Description: 初期スキーマの作成（既存テーブルの登録）
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = '0001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum type first (required before any table references it)
    op.execute("CREATE TYPE userrole AS ENUM ('admin', 'operator', 'viewer')")

    # users
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('username', sa.String(150), nullable=False, unique=True),
        sa.Column('email', sa.String(254), nullable=False, unique=True),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('role', sa.Enum('admin', 'operator', 'viewer', name='userrole', create_type=False), nullable=False, server_default='viewer'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_superuser', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_users_username', 'users', ['username'], unique=True)
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    # file_uploads
    op.create_table(
        'file_uploads',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('original_filename', sa.String(500), nullable=False),
        sa.Column('stored_filename', sa.String(500), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('mime_type', sa.String(100), nullable=False),
        sa.Column('storage_path', sa.String(1000), nullable=False),
        sa.Column('extracted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('extraction_status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('security_scan_status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('security_scan_result', sa.String(200), nullable=False, server_default=''),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_file_uploads_user_id', 'file_uploads', ['user_id'])

    # audit_logs (non-partitioned baseline)
    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('resource_type', sa.String(100), nullable=False),
        sa.Column('resource_id', sa.String(200), nullable=True),
        sa.Column('details', sa.String(1000), nullable=False, server_default=''),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_audit_logs_user_id', 'audit_logs', ['user_id'])
    op.create_index('ix_audit_logs_created_at', 'audit_logs', ['created_at'])

    # extraction_events
    op.create_table(
        'extraction_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('upload_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('file_uploads.id', ondelete='CASCADE'), nullable=False),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('message', sa.String(500), nullable=False, server_default=''),
        sa.Column('file_path', sa.String(1000), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='success'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_extraction_events_upload_id', 'extraction_events', ['upload_id'])

    # security_events
    op.create_table(
        'security_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('upload_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('file_uploads.id', ondelete='CASCADE'), nullable=True),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('severity', sa.String(20), nullable=False, server_default='info'),
        sa.Column('message', sa.String(500), nullable=False, server_default=''),
        sa.Column('details', sa.String(2000), nullable=False, server_default=''),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_security_events_upload_id', 'security_events', ['upload_id'])
    op.create_index('ix_security_events_created_at', 'security_events', ['created_at'])

    # pipeline_stages
    op.create_table(
        'pipeline_stages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('stage_name', sa.String(100), nullable=False),
        sa.Column('stage_order', sa.Integer(), nullable=False),
        sa.Column('description', sa.String(500), nullable=False, server_default=''),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # pipeline_runs
    op.create_table(
        'pipeline_runs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('stage_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('pipeline_stages.id', ondelete='CASCADE'), nullable=False),
        sa.Column('run_number', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='running'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('duration_seconds', sa.Float(), nullable=True),
        sa.Column('logs', sa.String(5000), nullable=False, server_default=''),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_pipeline_runs_stage_id', 'pipeline_runs', ['stage_id'])


def downgrade() -> None:
    op.drop_index('ix_pipeline_runs_stage_id', table_name='pipeline_runs')
    op.drop_table('pipeline_runs')
    op.drop_table('pipeline_stages')
    op.drop_index('ix_security_events_created_at', table_name='security_events')
    op.drop_index('ix_security_events_upload_id', table_name='security_events')
    op.drop_table('security_events')
    op.drop_index('ix_extraction_events_upload_id', table_name='extraction_events')
    op.drop_table('extraction_events')
    op.drop_index('ix_audit_logs_created_at', table_name='audit_logs')
    op.drop_index('ix_audit_logs_user_id', table_name='audit_logs')
    op.drop_table('audit_logs')
    op.drop_index('ix_file_uploads_user_id', table_name='file_uploads')
    op.drop_table('file_uploads')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_index('ix_users_username', table_name='users')
    op.drop_table('users')
    op.execute("DROP TYPE IF EXISTS userrole")
