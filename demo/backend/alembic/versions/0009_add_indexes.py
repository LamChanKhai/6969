"""
Revision: 0009_add_indexes
Description: パフォーマンス最適化用の複合インデックスを追加

Note: これらのインデックスは通常の CREATE INDEX（排他ロック付き）で作成されます。
大規模テーブルでは書き込みがブロックされるため、保守ウィンドウで実行してください。
"""

from typing import Sequence, Union

from alembic import op


revision: str = '0009_add_indexes'
down_revision: Union[str, None] = '0008_add_api_keys'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # file_uploads 複合インデックス
    op.create_index('idx_uploads_user_created', 'file_uploads', ['user_id', 'created_at'], unique=False)
    op.create_index('idx_uploads_scan_status', 'file_uploads', ['security_scan_status'], unique=False)
    op.create_index('idx_uploads_extracted', 'file_uploads', ['extracted', 'created_at'], unique=False)
    op.create_index('idx_uploads_hash', 'file_uploads', ['file_hash_sha256'], unique=False)

    # audit_logs 複合インデックス
    # idx_audit_time_range を削除 — ix_audit_logs_created_at と完全重複
    op.create_index('idx_audit_user_action', 'audit_logs', ['user_id', 'action'], unique=False)
    op.create_index('idx_audit_resource', 'audit_logs', ['resource_type', 'resource_id'], unique=False)

    # security_events 複合インデックス
    op.create_index('idx_events_severity_time', 'security_events', ['severity', 'created_at'], unique=False)
    op.create_index('idx_events_resolved', 'security_events', ['is_resolved', 'created_at'], unique=False)
    op.create_index('idx_events_type_severity', 'security_events', ['event_type', 'severity'], unique=False)

    # security_events.resolved_by FK 用インデックス（Warning 3 対応）
    op.create_index('ix_security_events_resolved_by', 'security_events', ['resolved_by'], unique=False)

    # pipeline_runs 複合インデックス
    op.create_index('idx_runs_stage_status', 'pipeline_runs', ['stage_id', 'status', 'created_at'], unique=False)
    op.create_index('idx_runs_status_time', 'pipeline_runs', ['status', 'started_at'], unique=False)

    # users 複合インデックス
    op.create_index('idx_users_role_active', 'users', ['role', 'is_active'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_users_role_active', table_name='users')
    op.drop_index('idx_runs_status_time', table_name='pipeline_runs')
    op.drop_index('idx_runs_stage_status', table_name='pipeline_runs')
    op.drop_index('ix_security_events_resolved_by', table_name='security_events')
    op.drop_index('idx_events_type_severity', table_name='security_events')
    op.drop_index('idx_events_resolved', table_name='security_events')
    op.drop_index('idx_events_severity_time', table_name='security_events')
    op.drop_index('idx_audit_resource', table_name='audit_logs')
    op.drop_index('idx_audit_user_action', table_name='audit_logs')
    op.drop_index('idx_uploads_hash', table_name='file_uploads')
    op.drop_index('idx_uploads_extracted', table_name='file_uploads')
    op.drop_index('idx_uploads_scan_status', table_name='file_uploads')
    op.drop_index('idx_uploads_user_created', table_name='file_uploads')
