# スキーマ変更設計書 — プロジェクト AAA

## 1. 現状スキーマ分析

### 1.1 データベースエンジン

| 項目 | 値 |
|------|-----|
| **エンジン** | PostgreSQL 15+ |
| **ORM** | SQLAlchemy 2.0 (async, asyncpg) |
| **マイグレーション** | Alembic (14ステップ、リニア) |

### 1.2 現状テーブル一覧（12ステップ後）

| テーブル | PK | FK | インデックス | 説明 |
|---------|-----|-----|-------------|------|
| users | UUID | - | ix_users_username, ix_users_email, idx_users_role_active | ユーザー管理 |
| file_uploads | UUID | user_id→users | ix_file_uploads_user_id, idx_uploads_user_created, idx_uploads_scan_status, idx_uploads_extracted, idx_uploads_hash | ファイルアップロード記録 |
| audit_logs | UUID (+ created_at) | user_id→users | idx_audit_user_action, idx_audit_resource, ix_audit_logs_created_at | 監査ログ（パーティション付き） |
| extraction_events | UUID | upload_id→file_uploads | ix_extraction_events_upload_id | アーカイブ展開イベント |
| security_events | UUID | upload_id→file_uploads, resolved_by→users | ix_security_events_upload_id, ix_security_events_created_at, idx_events_severity_time, idx_events_resolved, idx_events_type_severity, ix_security_events_resolved_by | セキュリティイベント |
| file_scan_results | UUID | upload_id→file_uploads | ix_scan_upload_status, ix_scan_type_created | ファイルスキャン結果 |
| pipeline_stages | UUID | - | - | DevSecOpsパイプラインステージ |
| pipeline_runs | UUID | stage_id→pipeline_stages | ix_pipeline_runs_stage_id, idx_runs_stage_status, idx_runs_status_time | パイプライン実行記録 |
| rate_limit_events | UUID | user_id→users | ix_rate_limit_ip_time, ix_rate_limit_user_time | レートリミット追跡 |
| api_keys | UUID | user_id→users | ix_apikeys_user_active | APIキー管理 |
| pipeline_executions | UUID | - | idx_pipeline_executions_status | パイプライン実行追跡 |
| pipeline_execution_steps | UUID | execution_id→pipeline_executions | ix_pipeline_execution_steps_execution_id, idx_pipeline_exec_steps_status | パイプライン実行ステップ |

### 1.3 現状の問題点（移行レビューからの残存課題）

| # | 問題 | 深刻度 | 説明 |
|---|------|--------|------|
| 1 | **security_events にパーティショニングなし** | 中 | security_events は継続的に増大するため、audit_logs と同様にパーティショニングが必要 |
| 2 | **pipeline_stages.stage_name に UNIQUE 制約なし** | 中 | 同名ステージの重複作成が可能。データ整合性に影響 |
| 3 | **pipeline_executions に CHECK 制約なし** | 低 | status カラムに有効値の制限がない |
| 4 | **pipeline_execution_steps に CHECK 制約なし** | 低 | status カラムに有効値の制限がない |
| 5 | **extraction_events に CHECK 制約なし** | 低 | status, event_type に有効値の制限がない |
| 6 | **security_events に PARTIAL インデックスなし** | 低 | 未解決イベントのクエリ頻度が高いが、is_resolved=false 用の部分インデックスがない |
| 7 | **audit_logs パーティションの PK が (id, created_at)** | 中 | 既存の FK (audit_logs.user_id → users.id) はパーティションキーを含まないが、これは問題なし（FK は PK を参照しないため）。ただし、アプリケーション側で id のみの参照がある場合は注意が必要 |

---

## 2. 必要なスキーマ変更

### 2.1 新規インデックス

| テーブル | インデックス名 | カラム | タイプ | 理由 |
|---------|---------------|--------|--------|------|
| security_events | idx_events_unresolved | (created_at DESC) WHERE (is_resolved = false) | B-tree 部分 | 未解決イベントの高速検索（ダッシュボードで頻出） |
| pipeline_stages | idx_stages_name_unique | (stage_name) | B-tree UNIQUE | 重複ステージ名の防止 |
| pipeline_executions | idx_exec_steps_status_time | (status, created_at DESC) | B-tree 複合 | 実行中パイプラインのタイムライン表示 |

### 2.2 制約追加

| テーブル | 制約名 | 式 | 説明 |
|---------|--------|-----|------|
| pipeline_stages | chk_stages_name_not_empty | stage_name <> '' | 空文字列のステージ名を禁止 |
| pipeline_executions | chk_exec_status | status IN ('running', 'completed', 'failed', 'cancelled') | 有効なステータスのみ |
| pipeline_executions | chk_exec_steps_range | current_step >= 0 AND current_step <= total_steps | ステップ数の整合性 |
| pipeline_execution_steps | chk_exec_step_status | status IN ('pending', 'running', 'completed', 'failed', 'skipped') | 有効なステータスのみ |
| extraction_events | chk_extract_status | status IN ('success', 'failed', 'pending', 'in_progress') | 有効なステータスのみ |
| extraction_events | chk_extract_event_type | event_type IN ('file_extracted', 'path_traversal_detected', 'extraction_failed', 'extraction_started') | 有効なイベント種別のみ |

### 2.3 security_events のパーティショニング

audit_logs と同様のテーブル置換方式で、`created_at` による RANGE パーティショニングを実施。

**パーティション戦略:**
- パーティション単位: 四半期
- 保持期間: 24ヶ月
- 自動作成: pg_cron を使用して四半期ごとに事前作成

---

## 3. データマイグレーション戦略

### 3.1 マイグレーション計画

| 順 | マイグレーション | 内容 | ダウンタイム |
|----|-----------------|------|-------------|
| 1 | 0013_add_constraints_and_indexes | 制約追加、UNIQUE制約、部分インデックス | なし（NOT VALID + VALIDATE） |
| 2 | 0014_partition_security_events | security_events のパーティショニング | 中（データ再配置必要） |

### 3.2 security_events パーティショニングの手順

1. パーティション付きの `security_events_partitioned` テーブルを作成
2. 初期パーティションを作成（過去1四半期 + 現在 + 未来1四半期）
3. 既存データを `INSERT ... SELECT` でコピー
4. 古いテーブルを DROP、新しいテーブルを RENAME
5. インデックス、FK、CHECK 制約を再作成
6. pg_cron ジョブで自動パーティション管理を設定

### 3.3 ロールバック手順

- **0013**: 制約の DROP は即時可能。UNIQUE 制約の DROP も即時可能。
- **0014**: パーティションをデタッチし、データをマージして非パーティションテーブルに戻す（0011 と同じパターン）

---

## 4. パフォーマンス影響分析

### 4.1 新規インデックスのストレージ影響

| インデックス | 推定サイズ（10万レコード） | 書き込みオーバーヘッド |
|-------------|--------------------------|----------------------|
| idx_events_unresolved (partial) | ~0.5 MB | 低（is_resolved=false のみのレコード） |
| idx_stages_name_unique | ~0.1 MB | 低（ほぼ静的データ） |
| idx_exec_steps_status_time | ~0.8 MB | 低 |
| **合計** | **~1.4 MB** | **全体的に低** |

### 4.2 クエリパフォーマンス改善の見込み

| クエリパターン | 改善前 | 改善後 | 改善率 |
|---------------|--------|--------|--------|
| 未解決セキュリティイベント一覧 | Seq Scan ~4ms | Partial Index Scan ~0.05ms | **80x** |
| パイプラインステージ名検索 | Seq Scan ~1ms | Unique Index Scan ~0.01ms | **100x** |
| 実行中パイプラインのタイムライン | Seq Scan ~2ms | Index Scan ~0.1ms | **20x** |

### 4.3 security_events パーティショニングの影響

| 項目 | パーティション前 | パーティション後 |
|------|-----------------|-----------------|
| DELETE（古データ削除） | 長時間の VACUUM | パーティション DETACH（即時） |
| 集計クエリ（全期間） | 全テーブルスキャン | パーティションプルーニング適用 |
| INSERT 性能 | 単一テーブル | ほぼ同等（PostgreSQL 15+ ではオーバーヘッド最小） |
| ストレージ | 単一テーブル + TOAST | パーティションごとに独立（旧パーティションの DROP で即解放） |

---

## 5. ER 図（変更後）

```mermaid
erDiagram
    users ||--o{ file_uploads : "has"
    users ||--o{ audit_logs : "creates"
    users ||--o{ api_keys : "owns"
    users ||--o| security_events : "resolves"
    users ||--o{ rate_limit_events : "triggers"
    file_uploads ||--o{ extraction_events : "generates"
    file_uploads ||--o{ security_events : "triggers"
    file_uploads ||--o{ file_scan_results : "scanned_by"
    pipeline_stages ||--o{ pipeline_runs : "executes"
    pipeline_executions ||--o{ pipeline_execution_steps : "contains"

    users {
        uuid id PK
        varchar username UK
        varchar email UK
        varchar hashed_password
        varchar role
        bool is_active
        bool is_superuser
        timestamptz last_login_at
        int login_attempts
        timestamptz locked_until
        int failed_login_attempts
        timestamptz created_at
        timestamptz updated_at
    }

    file_uploads {
        uuid id PK
        uuid user_id FK
        varchar original_filename
        varchar stored_filename
        int file_size
        varchar mime_type
        varchar storage_path
        varchar file_hash_sha256
        bool extracted
        varchar extraction_status
        varchar security_scan_status
        varchar security_scan_result
        bool archived
        timestamptz archived_at
        timestamptz created_at
    }

    audit_logs {
        uuid id PK
        timestamptz created_at PK_partition
        uuid user_id FK
        varchar action
        varchar resource_type
        varchar resource_id
        varchar details
        varchar ip_address
        varchar user_agent
        varchar session_id
        varchar request_id
    }

    extraction_events {
        uuid id PK
        uuid upload_id FK
        varchar event_type
        varchar message
        varchar file_path
        varchar status
        timestamptz created_at
    }

    security_events {
        uuid id PK
        timestamptz created_at PK_partition
        uuid upload_id FK
        uuid resolved_by FK
        varchar event_type
        varchar severity
        varchar message
        varchar details
        bool is_resolved
        timestamptz resolved_at
    }

    file_scan_results {
        uuid id PK
        uuid upload_id FK
        varchar scanner_name
        varchar scanner_version
        varchar scan_type
        varchar scan_status
        int threats_found
        text scan_details
        int duration_ms
        timestamptz created_at
    }

    pipeline_stages {
        uuid id PK
        varchar stage_name UK
        int stage_order
        varchar description
        bool is_active
        timestamptz created_at
    }

    pipeline_runs {
        uuid id PK
        uuid stage_id FK
        int run_number
        varchar status
        timestamptz started_at
        timestamptz finished_at
        float duration_seconds
        varchar logs
        timestamptz created_at
    }

    rate_limit_events {
        uuid id PK
        uuid user_id FK
        varchar ip_address
        varchar endpoint
        int request_count
        timestamptz window_start
        timestamptz window_end
        varchar action_taken
        timestamptz created_at
    }

    api_keys {
        uuid id PK
        uuid user_id FK
        varchar key_hash UK
        varchar key_prefix
        varchar name
        timestamptz expires_at
        timestamptz last_used_at
        bool is_active
        timestamptz created_at
    }

    pipeline_executions {
        uuid id PK
        varchar name
        int total_steps
        int current_step
        varchar status
        text step_logs
        text error_message
        timestamptz started_at
        timestamptz finished_at
        timestamptz created_at
    }

    pipeline_execution_steps {
        uuid id PK
        uuid execution_id FK
        int step_number
        varchar step_name
        varchar status
        text logs
        timestamptz started_at
        timestamptz finished_at
        float duration_seconds
        timestamptz created_at
    }
```

---

## 6. 意思決定ログ

| ID | 日付 | 決定事項 | 理由 | 決定者 |
|----|------|---------|------|--------|
| DD7 | 2026-05-30 | security_events を四半期パーティションに分割 | audit_logs と同様のデータ増大パターン。パーティション切り捨てで効率的なデータ管理 | DBA |
| DD8 | 2026-05-30 | pipeline_stages.stage_name に UNIQUE 制約を追加 | 同名ステージの重複防止。データ整合性の観点から必須 | DBA |
| DD9 | 2026-05-30 | security_events に部分インデックスを追加 | 未解決イベントのクエリ頻度が高い。部分インデックスでストレージと書き込みオーバーヘッドを最小化 | DBA |
| DD10 | 2026-05-30 | CHECK 制約は NOT VALID + VALIDATE パターン | ゼロダウンタイムデプロイ対応。既存データの検証ロックを回避 | DBA |
| DD11 | 2026-05-31 | マイグレーションの動的日付対応とダウングレード修正 | 2025年固定日付によるINSERT失敗の防止、およびダウングレード時のインデックス重複・PK不整合を解消 | DBA |
| DD12 | 2026-05-31 | テストスイートの HEAD (0014) 同期 | 0012-0014 の新規制約・インデックス・テーブルの検証を追加 | DBA |
| DD13 | 2026-05-31 | モデルとマイグレーションの乖離（PK）を許容 | パーティショニング対応のため DB 側は (id, created_at) の複合 PK を使用するが、アプリケーション（SQLAlchemy モデル）側は引き続き id のみを PK と定義。これは SQLAlchemy が単一カラム PK を想定している既存ロジックを壊さないための措置。 | Backend |
