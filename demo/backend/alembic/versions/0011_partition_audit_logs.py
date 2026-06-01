"""
Revision: 0011_partition_audit_logs
Description: audit_logs のパーティショニングを設定（テーブル置換方式）

既存の audit_logs テーブルをパーティション付きテーブルに置換し、
pg_cron ジョブで自動パーティション管理を行う。

Note: このマイグレーションは保守ウィンドウで実行してください。
大量のデータがある場合は、INSERT ... SELECT に時間がかかります。
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0011_partition_audit_logs'
down_revision: Union[str, None] = '0010_add_constraints'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Step 1: パーティション付きの新しいテーブルを作成
    op.execute("""
        CREATE TABLE audit_logs_partitioned (
            id UUID DEFAULT gen_random_uuid(),
            user_id UUID,
            action VARCHAR(100) NOT NULL,
            resource_type VARCHAR(100) NOT NULL,
            resource_id VARCHAR(200),
            details VARCHAR(1000) DEFAULT '',
            ip_address VARCHAR(45),
            user_agent VARCHAR(500),
            session_id VARCHAR(100),
            request_id VARCHAR(100),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            PRIMARY KEY (id, created_at)
        ) PARTITION BY RANGE (created_at)
    """)

    # Step 2: 初期パーティションを動的に作成（過去1ヶ月 + 現在 + 未来1ヶ月）
    op.execute("""
        DO $$
        DECLARE
            current_month_start DATE := date_trunc('month', current_date);
            last_month_start DATE := current_month_start - interval '1 month';
            next_month_start DATE := current_month_start + interval '1 month';
            partition_name TEXT;
        BEGIN
            partition_name := 'audit_logs_' || to_char(last_month_start, 'YYYY_MM');
            IF NOT EXISTS (SELECT 1 FROM pg_class WHERE relname = partition_name) THEN
                EXECUTE format(
                    'CREATE TABLE %I PARTITION OF audit_logs_partitioned FOR VALUES FROM (%L) TO (%L)',
                    partition_name, last_month_start, current_month_start
                );
            END IF;

            partition_name := 'audit_logs_' || to_char(current_month_start, 'YYYY_MM');
            IF NOT EXISTS (SELECT 1 FROM pg_class WHERE relname = partition_name) THEN
                EXECUTE format(
                    'CREATE TABLE %I PARTITION OF audit_logs_partitioned FOR VALUES FROM (%L) TO (%L)',
                    partition_name, current_month_start, next_month_start
                );
            END IF;

            partition_name := 'audit_logs_' || to_char(next_month_start, 'YYYY_MM');
            IF NOT EXISTS (SELECT 1 FROM pg_class WHERE relname = partition_name) THEN
                EXECUTE format(
                    'CREATE TABLE %I PARTITION OF audit_logs_partitioned FOR VALUES FROM (%L) TO (%L)',
                    partition_name, next_month_start, next_month_start + interval '1 month'
                );
            END IF;
        END $$
    """)

    # Step 3: 既存データを新しいテーブルにコピー
    op.execute("""
        INSERT INTO audit_logs_partitioned (id, user_id, action, resource_type, resource_id,
                                              details, ip_address, user_agent, session_id, request_id, created_at)
        SELECT id, user_id, action, resource_type, resource_id,
               details, ip_address, user_agent, session_id, request_id, created_at
        FROM audit_logs
    """)

    # Step 4: 古いテーブルを削除し、新しいテーブルにリネーム
    op.execute("DROP TABLE audit_logs")
    op.execute("ALTER TABLE audit_logs_partitioned RENAME TO audit_logs")

    # Step 5: インデックスを再作成
    op.execute("CREATE INDEX idx_audit_user_action ON audit_logs (user_id, action)")
    op.execute("CREATE INDEX idx_audit_resource ON audit_logs (resource_type, resource_id)")
    op.execute("CREATE INDEX ix_audit_logs_created_at ON audit_logs (created_at)")

    # Step 6: 外部キーを再作成
    op.execute("""
        ALTER TABLE audit_logs ADD CONSTRAINT fk_audit_user
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
    """)

    # Step 7: pg_cron ジョブ — 次月のパーティションを自動作成
    op.execute("""
        SELECT cron.schedule(
            'create-audit-logs-partition',
            '0 0 28 * *',
            $$
            DO $$
            DECLARE
                next_month_start DATE := date_trunc('month', current_date) + interval '1 month';
                next_month_end DATE := date_trunc('month', current_date) + interval '2 months';
                partition_name TEXT;
            BEGIN
                partition_name := 'audit_logs_' || to_char(next_month_start, 'YYYY_MM');
                IF NOT EXISTS (
                    SELECT 1 FROM pg_class WHERE relname = partition_name
                ) THEN
                    EXECUTE format(
                        'CREATE TABLE %I PARTITION OF audit_logs FOR VALUES FROM (%L) TO (%L)',
                        partition_name, next_month_start, next_month_end
                    );
                END IF;
            END $$
        $$
        );
    """)

    # Step 8: pg_cron ジョブ — 12ヶ月前のパーティションをデタッチしてアーカイブ
    op.execute("""
        SELECT cron.schedule(
            'archive-old-audit-logs',
            '0 3 1 * *',
            $$
            DO $$
            DECLARE
                cutoff_date DATE := date_trunc('month', current_date - interval '12 months');
                partition_name TEXT;
            BEGIN
                FOR partition_name IN
                    SELECT c.relname
                    FROM pg_inherits i
                    JOIN pg_class p ON p.oid = i.inhparent
                    JOIN pg_class c ON c.oid = i.inhrelid
                    WHERE p.relname = 'audit_logs'
                      AND c.relname LIKE 'audit_logs______'
                LOOP
                    IF to_date(substring(partition_name from 13), 'YYYY_MM') < cutoff_date THEN
                        EXECUTE format('ALTER TABLE audit_logs DETACH PARTITION %I', partition_name);
                        EXECUTE format(
                            'ALTER TABLE %I RENAME TO audit_logs_archive_%s',
                            partition_name, substring(partition_name from 13)
                        );
                    END IF;
                END LOOP;
            END $$
        $$
        );
    """)


def downgrade() -> None:
    # pg_cron ジョブを解除
    op.execute("SELECT cron.unschedule('create-audit-logs-partition')")
    op.execute("SELECT cron.unschedule('archive-old-audit-logs')")

    # パーティション付きテーブルを通常のテーブルに戻す
    # 各パーティションをデタッチ
    result = op.get_bind().execute(sa.text(
        "SELECT c.relname FROM pg_inherits i "
        "JOIN pg_class p ON p.oid = i.inhparent "
        "JOIN pg_class c ON c.oid = i.inhrelid "
        "WHERE p.relname = 'audit_logs'"
    ))
    for (partition_name,) in result:
        op.execute(f"ALTER TABLE audit_logs DETACH PARTITION {partition_name}")

    # デタッチされたパーティションのデータを一時テーブルにマージ
    # INCLUDING DEFAULTS INCLUDING CONSTRAINTS (not ALL) to avoid copying indexes
    op.execute("CREATE TABLE audit_logs_temp (LIKE audit_logs INCLUDING DEFAULTS INCLUDING CONSTRAINTS)")
    result = op.get_bind().execute(sa.text(
        "SELECT c.relname FROM pg_class c "
        "WHERE c.relname LIKE 'audit_logs______'"
    ))
    for (partition_name,) in result:
        op.execute(f"INSERT INTO audit_logs_temp SELECT * FROM {partition_name}")
        op.execute(f"DROP TABLE {partition_name}")

    # パーティション親テーブルを削除
    op.execute("DROP TABLE audit_logs")
    op.execute("ALTER TABLE audit_logs_temp RENAME TO audit_logs")

    # Restore original single-column PK (id only) — partitioned table had (id, created_at)
    op.execute("ALTER TABLE audit_logs DROP CONSTRAINT IF EXISTS audit_logs_pkey")
    op.execute("ALTER TABLE audit_logs ADD PRIMARY KEY (id)")

    # インデックスと制約を再作成
    op.execute("CREATE INDEX ix_audit_logs_user_id ON audit_logs (user_id)")
    op.execute("CREATE INDEX ix_audit_logs_created_at ON audit_logs (created_at)")
    op.execute("""
        ALTER TABLE audit_logs ADD CONSTRAINT audit_logs_user_id_fkey
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
    """)
