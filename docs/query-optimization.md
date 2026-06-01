# Query Optimization Recommendations

## Current Query Analysis

### 1. User Creation - Race Condition + Inefficient Lookup

**Location**: `gateway/views.py:51-69`

```python
# CURRENT (problematic)
user = User.objects.filter(username=request_data["username"]).first()
if not user:
    user = User.objects.create(**request_data)
user.set_password(request_data["password"])
user.save()
```

**Issues**:
1. **Race condition**: Two concurrent requests can both find `user=None` and create duplicates
2. **N+1 pattern**: Separate filter + create instead of atomic operation
3. **Missing select_for_update**: No row-level locking during check-then-create

**Optimized**:
```python
user, created = User.objects.get_or_create(
    username=request_data["username"],
    defaults={"email": request_data.get("email", "")}
)
user.set_password(request_data["password"])
user.save(update_fields=["password", "date_joined"])
```

**Expected Improvement**: Eliminates duplicate user creation under concurrent load. Reduces queries from 2 to 1 in the common case.

---

### 2. User Search - Unbounded Slicing

**Location**: `gateway/views.py:73-84`

```python
# CURRENT (problematic)
users = User.objects.filter(**request.data)[offset:offset+10]
```

**Issues**:
1. **Python-level slicing**: `[offset:offset+10]` fetches ALL matching rows into memory, then slices
2. **No LIMIT/OFFSET at DB level**: For large result sets, this causes excessive memory usage
3. **Dynamic filter injection**: `**request.data` allows arbitrary field filtering without validation
4. **No pagination metadata**: Client has no way to know total count or available pages

**Optimized**:
```python
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

class UserPagination(PageNumberPagination):
    page_size = 10
    max_page_size = 100
    page_size_query_param = 'page_size'

# In viewset:
pagination_class = UserPagination

def list(self, request):
    queryset = User.objects.all()
    # Validate filter fields explicitly
    allowed_fields = ['username', 'email', 'is_active']
    filters = {k: v for k, v in request.query_params.items() if k in allowed_fields}
    if filters:
        queryset = queryset.filter(**filters)
    queryset = queryset.select_related()  # Pre-fetch related data if needed
    page = self.paginate_queryset(queryset)
    if page is not None:
        serializer = UserSerializer(page, many=True)
        return self.get_paginated_response(serializer.data)
    serializer = UserSerializer(queryset, many=True)
    return Response(serializer.data)
```

**Expected Improvement**:
- Memory: O(10) instead of O(N) for result fetching
- Query time: Database-level LIMIT/OFFSET with index support
- Scalability: Handles millions of users without memory overflow

---

### 3. User Find Endpoint - Arbitrary Filter Injection

**Location**: `gateway/views.py:73-84`

```python
users = User.objects.filter(**request.data)[offset:offset+10]
```

**Security Issue**: Accepting raw `request.data` as filter kwargs allows:
- Filtering on internal fields (`is_staff`, `password`)
- Traversing relationships (`user__permissions__...`)
- Potential denial of service through complex queries

**Fix**: Whitelist allowed filter fields as shown above.

---

## Recommended Indexes

### For PostgreSQL (Post-Migration)

```sql
-- Core user lookups
CREATE INDEX idx_gateway_user_email ON gateway_user (email);
CREATE INDEX idx_gateway_user_username ON gateway_user (username);

-- Authentication optimization
CREATE INDEX idx_gateway_user_active_username ON gateway_user (username) WHERE is_active = true;
CREATE INDEX idx_gateway_user_active_email ON gateway_user (email) WHERE is_active = true;

-- Date-based queries
CREATE INDEX idx_gateway_user_date_joined ON gateway_user (date_joined DESC);

-- Session cleanup
CREATE INDEX idx_django_session_expire ON django_session (expire_date);
```

### For SQLite (Current)

SQLite will create these indexes automatically when you add `db_index=True` or `Index()` to the model:

```python
# gateway/models.py
class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=['email'], name='idx_user_email'),
            models.Index(fields=['username'], name='idx_user_username'),
            models.Index(fields=['date_joined'], name='idx_user_date_joined'),
        ]
        constraints = [
            models.UniqueConstraint(fields=['email'], name='uniq_user_email'),
        ]
```

## Django ORM Query Optimization

### 1. Use `select_related` and `prefetch_related`

```python
# If User has related objects (groups, user_permissions):
users = User.objects.select_related().prefetch_related(
    'groups', 'user_permissions'
)[:10]
```

### 2. Use `only()` or `defer()` for Partial Loading

```python
# Only load fields you need
users = User.objects.only('username', 'email')[:10]
```

### 3. Disable Unnecessary Features

```python
# superapp/settings.py
# Disable session persistence if not needed (reduces DB writes)
# SESSION_ENGINE = 'django.contrib.sessions.backends.cache'

# Disable admin log if not using admin
# LOGGING = {...}  # Reduce admin log writes
```

## Connection Pooling

### Current State
- uWSGI runs 6 processes x 4 threads = 24 concurrent workers
- Each worker opens a new DB connection per request (SQLite file lock contention)

### After PostgreSQL Migration
- Use Django's `CONN_MAX_AGE` for persistent connections
- Add PgBouncer for connection pooling in production

```python
# settings.py
DATABASES['default']['CONN_MAX_AGE'] = 60  # 60-second connection reuse
DATABASES['default']['CONN_HEALTH_CHECKS'] = True
```

## Slow Query Monitoring

### Enable Django Query Logging (Development)

```python
# settings.py (development only)
LOGGING = {
    'version': 1,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django.db.backends': {
            'level': 'DEBUG',
            'handlers': ['console'],
        },
    },
}
```

### Production Monitoring (PostgreSQL)

```sql
-- Enable pg_stat_statements extension
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Query top slow queries
SELECT query, calls, total_exec_time, mean_exec_time, rows
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 20;
```

## Summary of Expected Improvements

| Optimization | Current | After | Impact |
|-------------|---------|-------|--------|
| User creation | 2 queries + race condition | 1 atomic query | Correctness + 50% fewer queries |
| User listing | Loads all rows to memory | DB-level LIMIT/OFFSET | O(1) memory usage |
| Indexes | Primary key only | 5 targeted indexes | 10-100x faster lookups |
| Connection handling | New connection per request | Persistent connections | Reduced connection overhead |
| Filter injection | Arbitrary fields | Whitelisted fields | Security hardening |
