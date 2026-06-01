# Schema Review

## Current Schema

### `gateway_user` Table (Django Custom User Model)

Inferred from `gateway/models.py`:

```sql
-- Django-generated schema (SQLite)
CREATE TABLE gateway_user (
    pk INTEGER PRIMARY KEY AUTOINCREMENT,
    id UUID NOT NULL UNIQUE,
    password VARCHAR(128) NOT NULL,
    last_login TIMESTAMP NULL,
    is_superuser BOOLEAN NOT NULL,
    username VARCHAR(150) NOT NULL UNIQUE,
    first_name VARCHAR(150) NOT NULL,
    last_name VARCHAR(150) NOT NULL,
    email VARCHAR(254) NOT NULL,
    is_staff BOOLEAN NOT NULL,
    is_active BOOLEAN NOT NULL,
    date_added TIMESTAMP NOT NULL,
    -- Inherited from AbstractUser
);
```

### Django Auth Tables (Auto-created)
- `auth_permission`
- `auth_group`
- `auth_group_permissions`
- `django_admin_log`
- `django_content_type`
- `django_migrations`
- `django_session`

## Issues

| Table | Issue | Severity | Recommendation |
|-------|-------|----------|----------------|
| `gateway_user` | `email` lacks `unique` constraint | **HIGH** | Add `unique=True` to prevent duplicate accounts |
| `gateway_user` | No index on `email` for lookups | **MEDIUM** | Add database index on email field |
| `gateway_user` | `username` lookup in `UserViewSet.create` has race condition | **HIGH** | Use `get_or_create` with proper locking |
| `gateway_user` | No `last_login` tracking configured | **LOW** | Enable `UpdateLastLoginMiddleware` |
| All tables | SQLite lacks concurrent write support | **CRITICAL** | Migrate to PostgreSQL for production workloads |
| All tables | No foreign key enforcement in SQLite by default | **HIGH** | Enable FK constraints or migrate to PostgreSQL |
| `django_session` | No expiration/cleanup strategy documented | **MEDIUM** | Configure `django_cleanup` or periodic session purge |
| `gateway_user` | No soft-delete or audit trail | **LOW** | Add `deleted_at` timestamp and activity logging |

## Recommended Schema Changes

### 1. Add Email Uniqueness

```python
# gateway/models.py
class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)  # Add unique=True
```

### 2. Add Indexes

```python
class Meta:
    indexes = [
        models.Index(fields=['email'], name='idx_user_email'),
        models.Index(fields=['username'], name='idx_user_username'),
        models.Index(fields=['date_joined'], name='idx_user_date_joined'),
    ]
```

### 3. Fix Race Condition in User Creation

```python
# Replace the current create logic with:
user, created = User.objects.get_or_create(
    username=request_data["username"],
    defaults={
        "email": request_data.get("email", ""),
    }
)
user.set_password(request_data["password"])
user.save()
```

### 4. Add Missing Fields

```python
class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

## Impact Analysis

| Change | Read Impact | Write Impact | Downtime Required |
|--------|-------------|--------------|-------------------|
| Email unique constraint | Faster email lookups | Slower inserts (unique check) | Migration needed |
| Indexes | Significantly faster queries | Slightly slower writes | No downtime |
| Race condition fix | No change | Atomic operation | No downtime |
| PostgreSQL migration | Major improvement | Concurrent writes supported | Planned migration window |

## Rollback Procedure

1. Revert migration: `python manage.py migrate gateway <previous_migration>`
2. Restore from backup if data corruption occurs
3. Keep previous migration files for at least 2 weeks post-deploy
