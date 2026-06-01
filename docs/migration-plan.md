# Database Migration Plan: SQLite to PostgreSQL

## Why Migrate?

| Issue | SQLite | PostgreSQL |
|-------|--------|------------|
| Concurrent writes | NOT SUPPORTED | Full MVCC support |
| Connection handling | Single-writer, multi-reader | Connection pooling via PgBouncer |
| Data types | Limited (TEXT, INTEGER, REAL, BLOB) | Rich types (UUID, JSONB, ARRAY, etc.) |
| Foreign keys | Disabled by default | Enforced by default |
| Full-text search | Basic | Advanced (tsvector, tsquery) |
| JSON support | TEXT only | Native JSONB with indexing |
| Partitioning | NOT SUPPORTED | Native table partitioning |
| Replication | NOT SUPPORTED | Streaming replication, logical replication |
| Vacuum/Auto-vacuum | Manual | Automatic |
| MAX database size | 140 TB theoretical, practical limits | Unlimited |

## Migration Steps

### Phase 1: Preparation (Day 1-2)

#### 1.1 Install PostgreSQL

```yaml
# Add to docker-compose.yaml
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: superapp
      POSTGRES_USER: superapp_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U superapp_user -d superapp"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  pgdata:
```

#### 1.2 Add psycopg2 to Requirements

```txt
# requirements.txt additions
psycopg2-binary==2.9.9
dj-database-url==2.1.0
```

#### 1.3 Update Django Settings

```python
# superapp/settings.py - Database configuration

import dj_database_url
import os

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'superapp'),
        'USER': os.getenv('DB_USER', 'superapp_user'),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', 'postgres'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'OPTIONS': {
            'connect_timeout': 10,
            'options': '-c statement_timeout=30000',
        },
        'CONN_MAX_AGE': 60,  # Persistent connections
        'CONN_HEALTH_CHECKS': True,  # Django 4.1+
    }
}

# Connection pooling via PgBouncer (production)
# DATABASES['default']['HOST'] = 'pgbouncer'
# DATABASES['default']['PORT'] = '6432'
```

#### 1.4 Add Database Environment Variables

```bash
# .env file (do NOT commit to version control)
DB_NAME=superapp
DB_USER=superapp_user
DB_PASSWORD=<generate-strong-password>
DB_HOST=postgres
DB_PORT=5432
```

### Phase 2: Schema Migration (Day 3)

#### 2.1 Generate New Migrations

```bash
# After switching ENGINE, regenerate migrations
python manage.py makemigrations
python manage.py migrate --run-syncdb
```

#### 2.2 PostgreSQL-Specific Optimizations

```sql
-- init.sql - Run on PostgreSQL startup

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable pg_trgm for text search
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Optimize for Django workload
ALTER SYSTEM SET effective_cache_size = '4GB';
ALTER SYSTEM SET shared_buffers = '1GB';
ALTER SYSTEM SET work_mem = '16MB';
ALTER SYSTEM SET maintenance_work_mem = '512MB';
ALTER SYSTEM SET random_page_cost = 1.1;
ALTER SYSTEM SET effective_io_concurrency = 200;
ALTER SYSTEM SET max_connections = 100;
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;

-- Auto-vacuum tuning
ALTER SYSTEM SET autovacuum_max_workers = 3;
ALTER SYSTEM SET autovacuum_naptime = '60s';
ALTER SYSTEM SET autovacuum_vacuum_threshold = 50;
ALTER SYSTEM SET autovacuum_analyze_threshold = 50;
ALTER SYSTEM SET autovacuum_vacuum_scale_factor = 0.1;
ALTER SYSTEM SET autovacuum_analyze_scale_factor = 0.05;
```

### Phase 3: Data Migration (Day 4)

#### 3.1 Export from SQLite

```bash
# Option A: Django dump (recommended for small datasets)
python manage.py dumpdata --indent 2 --natural-foreign --natural-primary -e contenttypes -e auth.permission -e admin.logentry -e sessions.session > data_dump.json

# Option B: Direct SQLite to PostgreSQL (for larger datasets)
# Install pgloader
pgloader sqlite:///db.sqlite3 postgresql://superapp_user:password@localhost/superapp
```

#### 3.2 Import to PostgreSQL

```bash
# Option A: Django load
python manage.py loaddata data_dump.json

# Option B: pgloader handles this automatically
```

#### 3.3 Validate Migration

```bash
# Run Django checks
python manage.py check --deploy

# Verify record counts
python manage.py shell -c "
from gateway.models import User
from django.contrib.auth.models import Group, Permission
print(f'Users: {User.objects.count()}')
print(f'Groups: {Group.objects.count()}')
print(f'Permissions: {Permission.objects.count()}')
"

# Run tests
python manage.py test gateway
```

### Phase 4: Optimization (Day 5)

#### 4.1 Create Indexes

```sql
-- User table indexes
CREATE INDEX idx_gateway_user_email ON gateway_user USING btree (email);
CREATE INDEX idx_gateway_user_username ON gateway_user USING btree (username);
CREATE INDEX idx_gateway_user_date_joined ON gateway_user USING btree (date_joined);

-- Session table cleanup index
CREATE INDEX idx_django_session_expiry ON django_session (expire_date);

-- Update statistics after index creation
ANALYZE gateway_user;
ANALYZE django_session;
ANALYZE auth_permission;
```

#### 4.2 Set Up Connection Pooling (PgBouncer)

```ini
# pgbouncer.ini
[databases]
superapp = host=postgres port=5432 dbname=superapp

[pgbouncer]
listen_addr = *
listen_port = 6432
auth_type = md5
auth_file = /etc/pgbouncer/userlist.txt
pool_mode = transaction
max_client_conn = 500
default_pool_size = 25
min_pool_size = 5
reserve_pool_size = 5
reserve_pool_timeout = 3
server_idle_timeout = 600
server_lifetime = 3600
server_connect_timeout = 15
server_login_retry = 15
query_timeout = 30
query_wait_timeout = 120
client_idle_timeout = 0
logfile = /var/log/pgbouncer/pgbouncer.log
pidfile = /var/run/pgbouncer/pgbouncer.pid
admin_users = superapp_user
stats_users = superapp_user
```

### Phase 5: Testing & Cutover (Day 6-7)

#### 5.1 Load Testing

```bash
# Verify performance with pgbench or custom load tests
pgbench -i -s 10 superapp
pgbench -c 10 -j 2 -T 60 superapp
```

#### 5.2 Rollback Plan

```bash
# If migration fails, revert to SQLite:
# 1. Revert settings.py to SQLite configuration
# 2. Restore db.sqlite3 from backup
# 3. Remove psycopg2 dependency
# 4. Remove PostgreSQL service from docker-compose
```

## Docker Compose (Updated)

```yaml
services:
  app1:
    build:
      context: ./app1
      dockerfile: Dockerfile
    environment:
      - STORAGE_URL=http://app2
      - DB_NAME=superapp
      - DB_USER=superapp_user
      - DB_PASSWORD=${DB_PASSWORD}
      - DB_HOST=postgres
      - DB_PORT=5432
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy

  app2:
    build:
      context: ./app2
      dockerfile: Dockerfile
    volumes:
      - ./app2/flag.txt:/flag.txt:ro

  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: superapp
      POSTGRES_USER: superapp_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U superapp_user -d superapp"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  pgdata:
```

## Estimated Timeline

| Phase | Duration | Risk Level |
|-------|----------|------------|
| Preparation | 2 days | Low |
| Schema Migration | 1 day | Medium |
| Data Migration | 1 day | Medium |
| Optimization | 1 day | Low |
| Testing & Cutover | 2 days | Medium |
| **Total** | **7 days** | |
