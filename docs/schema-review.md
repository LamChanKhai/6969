# Database Schema Review

## Project Overview

Two-service architecture:
- **app1**: Django REST API (Django 5.2, SQLite) — user auth + file transport orchestration
- **app2**: PHP/Apache storage service — 7z archive extraction to filesystem

## Current Schema

### `gateway_user` Table (Django Auto-Generated)

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | UUID | PK, default uuid4 | Custom primary key |
| `password` | varchar(128) | NOT NULL | Hashed password |
| `last_login` | timestamp | NULLABLE | |
| `is_superuser` | boolean | DEFAULT false | |
| `username` | varchar(150) | UNIQUE, NOT NULL | |
| `first_name` | varchar(150) | BLANK | Unused |
| `last_name` | varchar(150) | BLANK | Unused |
| `is_staff` | boolean | DEFAULT false | |
| `is_active` | boolean | DEFAULT true | |
| `date_joined` | timestamp | NOT NULL | |
| `email` | varchar(254) | NOT NULL | No uniqueness constraint |

### Django Auth Tables (Implicit)

| Table | Purpose |
|-------|---------|
| `auth_group` | Group management |
| `auth_group_permissions` | Group-permission mapping |
| `auth_permission` | Permission definitions |
| `django_content_type` | ORM content type registry |
| `django_session` | Session storage |
| `django_admin_log` | Admin audit log |

---

## Issues

| Table | Issue | Severity | Recommendation |
|-------|-------|----------|----------------|
| All tables | SQLite as production database engine | **CRITICAL** | Migrate to PostgreSQL. SQLite lacks concurrency control, WAL scaling, and connection pooling needed for production. |
| `gateway_user` | No unique constraint on `email` | **HIGH** | Add `unique=True` on email field. Duplicate emails are possible. |
| `gateway_user` | Race condition: check-then-insert in `UserViewSet.create` | **HIGH** | `User.objects.filter(username=...).first()` followed by `User.objects.create()` is not atomic under concurrent requests. Use `get_or_create()` or a database-level unique constraint with retry logic. |
| `gateway_user` | Arbitrary field injection in `UserViewSet.find` | **HIGH** | `User.objects.filter(**request.data)` allows arbitrary keyword arguments from user input. An attacker can inject filter fields like `is_superuser__contains=1` or traverse relations. Whitelist allowed filter fields. |
| `gateway_user` | `email` not used as login identifier | **MEDIUM** | Set `USERNAME_FIELD = 'email'` on the model. Users currently authenticate by `username`, making `email` a dead field. |
| `django_session` | Sessions stored in DB with no expiration cleanup strategy | **MEDIUM** | Configure `SESSION_COOKIE_AGE` and run `clearsessions` periodically. Consider Redis for sessions. |
| `gateway_user` | No explicit indexes beyond PK and username unique | **MEDIUM** | Add indexes on commonly queried columns. |
| `gateway_user` | Unused fields (`first_name`, `last_name`) inherited from `AbstractUser` | **LOW** | Consider a custom user model extending `AbstractBaseUser` + `PermissionsMixin` for a leaner schema. |
| `gateway_user` | No index on `last_login` | **LOW** | Add index if querying by last-login is a pattern. |
| `gateway_user` | No `created_at` / `updated_at` audit timestamps | **LOW** | Add `auto_now_add` and `auto_now` fields for audit trails. |

---

## Query Pattern Analysis

### `UserViewSet.create()` — Race Condition

```python
# views.py:58-66 — CURRENT (vulnerable)
user = User.objects.filter(username=request_data["username"]).first()
if not user:
    user = User.objects.create(**request_data)
user.set_password(request_data["password"])
user.save()
```

**Problem**: Between the `.filter()` check and `.create()`, another request can create the same username, causing an integrity error. Additionally, `set_password()` + `save()` runs outside the `transaction.atomic()` block's protection for the create path, and the password is always overwritten even on an existing user.

**Fix**:
```python
user, created = User.objects.get_or_create(username=request_data["username"])
user.set_password(request_data["password"])
user.save()
```

### `UserViewSet.find()` — Injection + Missing Pagination

```python
# views.py:81 — CURRENT (vulnerable)
users = User.objects.filter(**request.data)[offset:offset+10]
```

**Problem 1**: `**request.data` passes arbitrary POST body keys as ORM filter kwargs. Attackers can inject relation traversals or internal fields.

**Problem 2**: Python-level slicing (`[offset:offset+10]`) fetches all matching rows into memory before discarding most of them. For large tables this is a severe performance issue.

**Fix**:
```python
ALLOWED_FILTERS = {"username", "email", "is_active"}
filter_kwargs = {k: v for k, v in request.data.items() if k in ALLOWED_FILTERS}
users = User.objects.filter(**filter_kwargs)[offset:offset+10]
# Better: use Django Paginator or offset/limit at the ORM level
users = User.objects.filter(**filter_kwargs).order_by('id')[offset:offset+10]
```

---

## Recommended Schema Changes

### 1. Add email uniqueness

```python
# gateway/models.py
class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)  # Add unique=True
```

Migration:
```python
# New migration
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [('gateway', '0001_initial')]
    operations = [
        migrations.AlterField(
            model_name='user',
            name='email',
            field=models.EmailField(max_length=254, unique=True),
        ),
    ]
```

### 2. Recommended lean custom user model (future refactor)

```python
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
import uuid

class CustomUserManager(models.Manager):
    def create_user(self, email, password=None, **kwargs):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **kwargs)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **kwargs):
        kwargs.setdefault('is_staff', True)
        kwargs.setdefault('is_superuser', True)
        return self.create_user(email, password, **kwargs)

class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, db_index=True)
    username = models.CharField(max_length=150, unique=True, db_index=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    objects = CustomUserManager()
```

### 3. Recommended indexes (for PostgreSQL migration)

```sql
-- Core lookups
CREATE INDEX idx_gateway_user_email ON gateway_user (email);
CREATE INDEX idx_gateway_user_username ON gateway_user (username);

-- Auth-related queries
CREATE INDEX idx_gateway_user_is_active ON gateway_user (is_active) WHERE is_active = true;

-- Session cleanup
CREATE INDEX idx_django_session_expire_date ON django_session (expire_date);
```

### 4. PostgreSQL Migration Settings

```python
# superapp/settings.py — replace SQLite config
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DB_NAME', default='superapp'),
        'USER': env('DB_USER', default='postgres'),
        'PASSWORD': env('DB_PASSWORD'),
        'HOST': env('DB_HOST', default='localhost'),
        'PORT': env('DB_PORT', default='5432'),
        'OPTIONS': {
            'connect_timeout': 10,
            'options': '-c statement_timeout=30000',
        },
    }
}

# Connection pooling via PgBouncer recommended for production
```

---

## Impact Analysis

| Change | Read Impact | Write Impact | Risk |
|--------|-------------|--------------|------|
| Email unique constraint | Faster email lookups | Rejects duplicate emails | Medium — may block existing duplicates |
| `get_or_create` for user creation | No change | Atomic upsert, eliminates race condition | Low |
| Whitelist filter fields in `find` | No change | No change | Low — may remove some filter flexibility |
| ORM-level pagination | Dramatically reduced memory usage | No change | Low |
| Custom user model | Smaller rows, faster scans | Migration required | High — breaking change to auth flows |
| PostgreSQL migration | Concurrent reads, connection pooling | WAL-based writes, MVCC | Medium — requires downtime window |
| Session to Redis | Sub-millisecond session reads | Offloads DB writes | Low — drop-in with django-redis |

---

## Rollback Procedures

1. **Email unique constraint**: If existing duplicates exist, deduplicate first:
    ```sql
    DELETE FROM gateway_user
    WHERE ctid NOT IN (
        SELECT MIN(ctid) FROM gateway_user GROUP BY email
    );
    ```
    Rollback: `ALTER TABLE gateway_user DROP CONSTRAINT gateway_user_email_key;`

2. **Custom user model**: Maintain backward migration that restores `AbstractUser` inheritance. Keep old migration files.

3. **PostgreSQL migration**: Keep SQLite backup before migration. Use `pg_dump` after migration for point-in-time recovery.

---

## Capacity Planning Notes

- **Current**: SQLite single-file DB — suitable for development only
- **Expected growth**: If user count exceeds ~10K or concurrent connections exceed ~50, PostgreSQL is mandatory
- **Recommended PostgreSQL sizing** (starting point):
  - `shared_buffers`: 25% of RAM
  - `effective_cache_size`: 50% of RAM
  - `work_mem`: 4-8 MB (adjust based on complex query count)
  - `maintenance_work_mem`: 512 MB - 1 GB
  - `max_connections`: 100 (via PgBouncer pool)
- **Backup strategy**: `pg_basebackup` for full backups + WAL archiving for PITR
- **Monitoring**: Enable `pg_stat_statements` extension for query performance tracking
