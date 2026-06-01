# Handoff to Cloud Expert — DBA スキーマ変更設計ステップ（プロジェクト AAA）

## ステータス: COMPLETE

## 完了した作業

DBAエキスパートとして、migration review で特定された残存課題に対するスキーマ変更設計を完了しました。

### 実施した分析

1. **移行レビュー（review_migration_review.md）の残存課題を分析** — 12ステップ完了後の追加改善点を特定
2. **7つの残存問題の特定** — security_eventsパーティショニング欠如、pipeline_stagesのUNIQUE制約欠如、CHECK制約の欠如など
3. **2つの新規マイグレーションファイルを作成** — 0013（制約・インデックス）、0014（security_eventsパーティショニング）

### 作成したマイグレーション

| マイグレーション | 内容 | ダウンタイム |
|-----------------|------|-------------|
| `0013_add_constraints_and_indexes` | pipeline_stages.stage_name UNIQUE制約、pipeline_executions/execution_steps/extraction_events CHECK制約、security_events部分インデックス、pipeline_executions複合インデックス | なし（NOT VALID + VALIDATEパターン） |
| `0014_partition_security_events` | security_eventsの四半期RANGEパーティショニング（テーブル置換方式）、pg_cron自動管理 | 中（データ再配置必要、保守ウィンドウ推奨） |

### 出力ファイル一覧

| ファイルパス | 説明 |
|-------------|------|
| `docs/03_dba/schema_changes_aaa.md` | スキーマ変更設計書（更新済み） |
| `demo/backend/alembic/versions/0013_add_constraints_and_indexes.py` | 制約追加、UNIQUE制約、部分インデックス |
| `demo/backend/alembic/versions/0014_partition_security_events.py` | security_eventsパーティショニング |

### マイグレーションチェーン（14ステップ完了）

```
0001_initial_schema
  → 0002_add_file_integrity
    → 0003_add_rate_limiting
      → 0004_add_scan_results
        → 0005_add_audit_tracing
          → 0006_add_security_resolution
            → 0007_add_user_security_fields
              → 0008_add_api_keys
                → 0009_add_indexes
                  → 0010_add_constraints
                    → 0011_partition_audit_logs
                      → 0012_add_pipeline_executions
                        → 0013_add_constraints_and_indexes ← 新規
                          → 0014_partition_security_events ← 新規
```

## クラウドインフラ設計に必要な情報

### データベース要件

| 項目 | 値 | 説明 |
|------|-----|------|
| **エンジン** | PostgreSQL 15+ | async/await対応、パーティショニング必須 |
| **推奨インスタンス** | db.r6g.xlarge (4 vCPU, 32GB RAM) | shared_buffers 1GB, effective_cache_size 2GB |
| **ストレージ** | GP3 SSD, 100GB初期、3000 IOPS | 月次約5-10GB増大見込み |
| **マルチAZ** | はい | 高可用性のためにシンクロナスレプリケーション |
| **バックアップ** | 自動バックアップ30日間 + WALアーカイブ | RPO 15分達成のため |
| **接続プール** | PgBouncer (transaction mode) | max_connections 100 |
| **モニタリング** | pg_stat_statements, pg_cron | クエリ統計と自動メンテナンス |

### 必須拡張

- **pg_cron** — audit_logsとsecurity_eventsのパーティション自動管理に必要。RDSの場合はパラメータグループで有効化

### セキュリティ要件

- VPC内プライベートサブネットに配置
- セキュリティグループ: アプリケーションサブネットからのみ5432/tcp許可
- SSL/TLS接続必須

## 注意事項

1. **0013はゼロダウンタイム対応** — CHECK制約は NOT VALID + VALIDATE パターンを使用。UNIQUE制約は pipeline_stages がほぼ静的データのため影響最小。
2. **0014は保守ウィンドウで実行** — security_events のパーティショニングはテーブル置換方式であり、DROP + RENAME 中に書き込みがブロックされます。
3. **pg_cron拡張の必須** — 0011と0014の両方でpg_cronを使用しています。Cloud ExpertがRDSパラメータグループで有効化してください。
4. **パーティションPKの注意** — audit_logsとsecurity_eventsのパーティションPKは `(id, created_at)` です。アプリケーション側で `id` のみで参照するクエリは `created_at` の条件も追加する必要があります。

## 未解決事項

- パーティショニングの実際のデータボリュームに基づく最適化（本番運用後に評価）
- file_scan_results の scan_details（TEXT型）の最大サイズ制限の検討

## 次のステップのタスク

### ステップ3: クラウドインフラ設計（Cloud Expert）

1. **クラウドアーキテクチャ設計** — PostgreSQL RDS、PgBouncer、読み取りレプリカ
2. **ネットワーク設計** — VPC、サブネット、セキュリティグループ
3. **スケーラビリティ・耐障害性** — マルチAZ、バックアップ、DR計画
4. **CI/CDパイプライン** — Alembicマイグレーション（14ステップ）のデプロイ統合

---

**DBAステップ完了。Cloud Expertステップへ引き渡し。**
