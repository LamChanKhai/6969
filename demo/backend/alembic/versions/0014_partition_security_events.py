"""
Revision: 0014_partition_security_events
Description: security_events のパーティショニングを設定（テーブル置換方式）

既存の security_events テーブルをパーティション付きテーブルに置換し、
pg_cron ジョブで自動パーティション管理を行う。

Note: このマイグレーションは保守ウィンドウで実行してください。
大量のデータがある場合は、INSERT ... SELECT に時間がかかります。
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0014_partition_security_events'
down_revision: Union[str, None] = '0013_add_constraints_and_indexes'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Step 1: パーティション付きの新しいテーブルを作成
    op.execute("""
        CREATE TABLE security_events_partitioned (
            id UUID DEFAULT gen_random_uuid(),
            upload_id UUID,
            event_type VARCHAR(50) NOT NULL,
            severity VARCHAR(20) NOT NULL DEFAULT 'info',
            message VARCHAR(500) NOT NULL DEFAULT '',
            details VARCHAR(2000) NOT NULL DEFAULT '',
            is_resolved BOOLEAN NOT NULL DEFAULT false,
            resolved_at TIMESTAMPTZ,
            resolved_by UUID,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            PRIMARY KEY (id, created_at)
        ) PARTITION BY RANGE (created_at)
    """)

    # Step 2: 初期パーティションを動的に作成（過去1四半期 + 現在 + 未来1四半期）
    op.execute("""
        DO $$
        DECLARE
            current_year INT := EXTRACT(YEAR FROM current_date)::INT;
            current_month INT := EXTRACT(MONTH FROM current_date)::INT;
            curr_q INT;
            prev_q_start DATE;
            curr_q_start DATE;
            next_q_start DATE;
            next_q_end DATE;
            partition_name TEXT;
        BEGIN
            curr_q := CASE
                WHEN current_month <= 3 THEN 1
                WHEN current_month <= 6 THEN 2
                WHEN current_month <= 9 THEN 3
                ELSE 4
            END;

            -- Previous quarter
            IF curr_q = 1 THEN
                prev_q_start := MAKE_DATE(current_year - 1, 10, 1);
            ELSE
                prev_q_start := MAKE_DATE(current_year, (curr_q - 1) * 3 + 1, 1);
            END IF;
            curr_q_start := MAKE_DATE(current_year, curr_q * 3 - 2, 1);

            -- Current quarter
            next_q_start := MAKE_DATE(current_year, curr_q * 3 + 1, 1);

            -- Next quarter
            IF curr_q = 4 THEN
                next_q_end := MAKE_DATE(current_year + 1, 4, 1);
            ELSE
                next_q_end := MAKE_DATE(current_year, (curr_q + 1) * 3 + 1, 1);
            END IF;

            -- Create previous quarter partition
            partition_name := 'security_events_' ||
                CASE WHEN curr_q = 1 THEN current_year - 1 ELSE current_year END ||
                '_q' || CASE WHEN curr_q = 1 THEN 4 ELSE curr_q - 1 END;
            IF NOT EXISTS (SELECT 1 FROM pg_class WHERE relname = partition_name) THEN
                EXECUTE format(
                    'CREATE TABLE %I PARTITION OF security_events_partitioned FOR VALUES FROM (%L) TO (%L)',
                    partition_name, prev_q_start, curr_q_start
                );
            END IF;

            -- Create current quarter partition
            partition_name := 'security_events_' || current_year || '_q' || curr_q;
            IF NOT EXISTS (SELECT 1 FROM pg_class WHERE relname = partition_name) THEN
                EXECUTE format(
                    'CREATE TABLE %I PARTITION OF security_events_partitioned FOR VALUES FROM (%L) TO (%L)',
                    partition_name, curr_q_start, next_q_start
                );
            END IF;

            -- Create next quarter partition
            partition_name := 'security_events_' ||
                CASE WHEN curr_q = 4 THEN current_year + 1 ELSE current_year END ||
                '_q' || CASE WHEN curr_q = 4 THEN 1 ELSE curr_q + 1 END;
            IF NOT EXISTS (SELECT 1 FROM pg_class WHERE relname = partition_name) THEN
                EXECUTE format(
                    'CREATE TABLE %I PARTITION OF security_events_partitioned FOR VALUES FROM (%L) TO (%L)',
                    partition_name, next_q_start, next_q_end
                );
            END IF;
        END $$
    """)

    # Step 3: 既存データを新しいテーブルにコピー
    op.execute("""
        INSERT INTO security_events_partitioned (
            id, upload_id, event_type, severity, message, details,
            is_resolved, resolved_at, resolved_by, created_at
        )
        SELECT id, upload_id, event_type, severity, message, details,
               is_resolved, resolved_at, resolved_by, created_at
        FROM security_events
    """)

    # Step 4: 古いテーブルを削除し、新しいテーブルにリネーム
    op.execute("DROP TABLE security_events")
    op.execute("ALTER TABLE security_events_partitioned RENAME TO security_events")

    # Step 5: インデックスを再作成
    op.execute("CREATE INDEX ix_security_events_upload_id ON security_events (upload_id)")
    op.execute("CREATE INDEX ix_security_events_created_at ON security_events (created_at)")
    op.execute("CREATE INDEX idx_events_severity_time ON security_events (severity, created_at)")
    op.execute("CREATE INDEX idx_events_resolved ON security_events (is_resolved, created_at)")
    op.execute("CREATE INDEX idx_events_type_severity ON security_events (event_type, severity)")
    op.execute("CREATE INDEX ix_security_events_resolved_by ON security_events (resolved_by)")

    # Step 6: 部分インデックス: 未解決イベント用（0013 で追加済み）
    op.execute("""
        CREATE INDEX idx_events_unresolved
        ON security_events (created_at DESC)
        WHERE (is_resolved = false)
    """)

    # Step 7: 外部キーを再作成
    op.execute("""
        ALTER TABLE security_events ADD CONSTRAINT fk_security_events_upload
            FOREIGN KEY (upload_id) REFERENCES file_uploads(id) ON DELETE CASCADE
    """)
    op.execute("""
        ALTER TABLE security_events ADD CONSTRAINT fk_security_events_resolved_by
            FOREIGN KEY (resolved_by) REFERENCES users(id) ON DELETE SET NULL
    """)

    # Step 8: CHECK 制約を再作成
    op.execute("""
        ALTER TABLE security_events ADD CONSTRAINT chk_events_severity
            CHECK (severity IN ('info', 'warning', 'high', 'critical')) NOT VALID
    """)
    op.execute("ALTER TABLE security_events VALIDATE CONSTRAINT chk_events_severity")

    # Step 9: pg_cron ジョブ — 次四半期のパーティションを自動作成
    op.execute("""
        SELECT cron.schedule(
            'create-security-events-partition',
            '0 0 1 */3 *',
            $$
            DO $$
            DECLARE
                next_q_start DATE;
                next_q_end DATE;
                partition_name TEXT;
                current_year INT;
                next_year INT;
                q_num INT;
            BEGIN
                current_year := EXTRACT(YEAR FROM current_date)::INT;
                q_num := CASE
                    WHEN EXTRACT(MONTH FROM current_date)::INT <= 3 THEN 1
                    WHEN EXTRACT(MONTH FROM current_date)::INT <= 6 THEN 2
                    WHEN EXTRACT(MONTH FROM current_date)::INT <= 9 THEN 3
                    ELSE 4
                END;

                IF q_num = 4 THEN
                    next_q_start := MAKE_DATE(current_year + 1, 1, 1);
                    next_q_end := MAKE_DATE(current_year + 1, 4, 1);
                    partition_name := 'security_events_' || (current_year + 1) || '_q1';
                ELSE
                    next_q_start := MAKE_DATE(current_year, q_num * 3 + 1, 1);
                    next_q_end := MAKE_DATE(current_year, (q_num + 1) * 3 + 1, 1);
                    partition_name := 'security_events_' || current_year || '_q' || (q_num + 1);
                END IF;

                IF NOT EXISTS (
                    SELECT 1 FROM pg_class WHERE relname = partition_name
                ) THEN
                    EXECUTE format(
                        'CREATE TABLE %I PARTITION OF security_events FOR VALUES FROM (%L) TO (%L)',
                        partition_name, next_q_start, next_q_end
                    );
                END IF;
            END $$
        $$
        );
    """)

    # Step 10: pg_cron ジョブ — 24ヶ月前のパーティションをデタッチしてアーカイブ
    op.execute("""
        SELECT cron.schedule(
            'archive-old-security-events',
            '0 4 1 1,4,7,10 *',
            $$
            DO $$
            DECLARE
                cutoff_year INT := EXTRACT(YEAR FROM current_date - interval '24 months')::INT;
                cutoff_month INT := EXTRACT(MONTH FROM current_date - interval '24 months')::INT;
                cutoff_q INT;
                partition_name TEXT;
                part_year INT;
                part_q INT;
            BEGIN
                cutoff_q := CASE
                    WHEN cutoff_month <= 3 THEN 1
                    WHEN cutoff_month <= 6 THEN 2
                    WHEN cutoff_month <= 9 THEN 3
                    ELSE 4
                END;

                FOR partition_name IN
                    SELECT c.relname
                    FROM pg_inherits i
                    JOIN pg_class p ON p.oid = i.inhparent
                    JOIN pg_class c ON c.oid = i.inhrelid
                    WHERE p.relname = 'security_events'
                      AND c.relname LIKE 'security_events______q%'
                LOOP
                    part_year := substring(partition_name from 19 for 4)::INT;
                    part_q := substring(partition_name from 24)::INT;

                    IF (part_year < cutoff_year) OR
                       (part_year = cutoff_year AND part_q < cutoff_q) THEN
                        EXECUTE format('ALTER TABLE security_events DETACH PARTITION %I', partition_name);
                        EXECUTE format(
                            'ALTER TABLE %I RENAME TO security_events_archive_%s',
                            partition_name,
                            substring(partition_name from 19)
                        );
                    END IF;
                END LOOP;
            END $$
        $$
        );
    """)


def downgrade() -> None:
    # pg_cron ジョブを解除
    op.execute("SELECT cron.unschedule('create-security-events-partition')")
    op.execute("SELECT cron.unschedule('archive-old-security-events')")

    # パーティション付きテーブルを通常のテーブルに戻す
    # 各パーティションをデタッチ
    result = op.get_bind().execute(sa.text(
        "SELECT c.relname FROM pg_inherits i "
        "JOIN pg_class p ON p.oid = i.inhparent "
        "JOIN pg_class c ON c.oid = i.inhrelid "
        "WHERE p.relname = 'security_events'"
    ))
    for (partition_name,) in result:
        op.execute(f"ALTER TABLE security_events DETACH PARTITION {partition_name}")

    # デタッチされたパーティションのデータを一時テーブルにマージ
    # INCLUDING DEFAULTS INCLUDING CONSTRAINTS (not ALL) to avoid copying indexes
    op.execute("CREATE TABLE security_events_temp (LIKE security_events INCLUDING DEFAULTS INCLUDING CONSTRAINTS)")
    result = op.get_bind().execute(sa.text(
        "SELECT c.relname FROM pg_class c "
        "WHERE c.relname LIKE 'security_events______q%'"
    ))
    for (partition_name,) in result:
        op.execute(f"INSERT INTO security_events_temp SELECT * FROM {partition_name}")
        op.execute(f"DROP TABLE {partition_name}")

    # パーティション親テーブルを削除
    op.execute("DROP TABLE security_events")
    op.execute("ALTER TABLE security_events_temp RENAME TO security_events")

    # Restore original single-column PK (id only) — partitioned table had (id, created_at)
    op.execute("ALTER TABLE security_events DROP CONSTRAINT IF EXISTS security_events_pkey")
    op.execute("ALTER TABLE security_events ADD PRIMARY KEY (id)")

    # インデックスと制約を再作成
    op.execute("CREATE INDEX ix_security_events_upload_id ON security_events (upload_id)")
    op.execute("CREATE INDEX ix_security_events_created_at ON security_events (created_at)")
    op.execute("CREATE INDEX idx_events_severity_time ON security_events (severity, created_at)")
    op.execute("CREATE INDEX idx_events_resolved ON security_events (is_resolved, created_at)")
    op.execute("CREATE INDEX idx_events_type_severity ON security_events (event_type, severity)")
    op.execute("CREATE INDEX ix_security_events_resolved_by ON security_events (resolved_by)")
    op.execute("""
        CREATE INDEX idx_events_unresolved
        ON security_events (created_at DESC)
        WHERE (is_resolved = false)
    """)
    op.execute("""
        ALTER TABLE security_events ADD CONSTRAINT security_events_upload_id_fkey
            FOREIGN KEY (upload_id) REFERENCES file_uploads(id) ON DELETE CASCADE
    """)
    op.execute("""
        ALTER TABLE security_events ADD CONSTRAINT security_events_resolved_by_fkey
            FOREIGN KEY (resolved_by) REFERENCES users(id) ON DELETE SET NULL
    """)
    op.execute("""
        ALTER TABLE security_events ADD CONSTRAINT chk_events_severity
            CHECK (severity IN ('info', 'warning', 'high', 'critical')) NOT VALID
    """)
    op.execute("ALTER TABLE security_events VALIDATE CONSTRAINT chk_events_severity")
