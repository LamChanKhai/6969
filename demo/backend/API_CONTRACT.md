# API Contract — SuperApp Demo Phase

## Overview

| Item | Detail |
|------|--------|
| **Project** | SuperApp Demo Phase |
| **Base URL** | `http://localhost:8000` |
| **Auth** | JWT Bearer Token (djangorestframework-simplejwt) |
| **Content-Type** | `application/json` (except file upload: `multipart/form-data`) |
| **Database** | SQLite3 |

---

## Authentication Flow

### 1. Register User

**POST** `/gateway/user/`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| username | string | Yes | Unique username |
| email | string | No | User email address |
| password | string | Yes | User password (meets Django validators) |

**Success Response** `200 OK`
```json
"demo_user1"
```

**Error Response** `400 Bad Request`
```json
{
    "username": ["A user with that username already exists."]
}
```

**Auth Required**: No

---

### 2. Obtain JWT Token

**POST** `/auth/token/`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| username | string | Yes | Registered username |
| password | string | Yes | User password |

**Success Response** `200 OK`
```json
{
    "access": "eyJhbGciOiJIUzI1NiIs...",
    "refresh": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Error Response** `401 Unauthorized`
```json
{
    "detail": "No active account found with the given credentials"
}
```

**Auth Required**: No

---

### 3. Refresh JWT Token

**POST** `/auth/refresh-token/`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| refresh | string | Yes | Refresh token from login |

**Success Response** `200 OK`
```json
{
    "access": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Error Response** `401 Unauthorized`
```json
{
    "detail": "Token is invalid or expired",
    "code": "token_not_valid"
}
```

**Auth Required**: No

---

## Gateway Endpoints

### 4. File Upload & Transport

**POST** `/gateway/transport/`

| Header | Value |
|--------|-------|
| Authorization | `Bearer <access_token>` |

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| file | file | Yes | ZIP file containing only allowed extensions |

**Allowed Extensions**: `.txt`, `.docx`, `.png`, `.jpg`, `.jpeg`

**Success Response** `200 OK`
```json
"OK"
```

**Error Responses**
- `200 OK` — `"Invalid file"` (disallowed extension inside ZIP)
- `401 Unauthorized` — Missing or invalid token
- `400 Bad Request` — Missing file field

**Auth Required**: Yes (JWT Bearer)

---

### 5. Health Check

**GET** `/gateway/health/`

| Query Param | Type | Default | Description |
|-------------|------|---------|-------------|
| module | string | `/health.php` | Path to check on App2 |

**Success Response** `200 OK`
```json
"OK"
```

**Error Response** `200 OK`
```json
"ERR"
```

**Auth Required**: No

---

### 6. User Search

**POST** `/gateway/user/find/`

| Header | Value |
|--------|-------|
| Authorization | `Bearer <access_token>` |

| Query Param | Type | Default | Description |
|-------------|------|---------|-------------|
| offset | integer | `0` | Pagination offset |

| Body Field | Type | Required | Description |
|------------|------|----------|-------------|
| (any User field) | varies | No | Filter kwargs (e.g. `username`, `email`) |

**Success Response** `200 OK`
```json
[
    {
        "username": "demo_user1",
        "email": "demo1@superapp.local"
    }
]
```

**Auth Required**: Yes (JWT Bearer)

---

## App2 Endpoints (Internal — not exposed externally)

### 7. File Storage & Extraction

**POST** `/storage.php`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | string | Yes | User UUID (storage directory name) |
| file | file | Yes | ZIP file to extract |

**Behavior**: Creates `storage/<id>/` directory, extracts ZIP contents using 7z CLI.

**Response**: `200 OK` (empty body on success)

**Auth Required**: No (internal service)

---

### 8. App2 Health Check

**GET** `/health.php`

**Response**: `200 OK` (empty body)

**Auth Required**: No

---

## Demo User Credentials (Pre-seeded)

| Username | Email | Password |
|----------|-------|----------|
| demo_user1 | demo1@superapp.local | DemoPass123! |
| demo_user2 | demo2@superapp.local | DemoPass456! |
| demo_user3 | demo3@superapp.local | DemoPass789! |

---

## Demo Flow (curl examples)

```bash
# 1. Register user
curl -X POST http://localhost:8000/gateway/user/ \
  -H "Content-Type: application/json" \
  -d '{"username":"demo_user1","email":"demo1@superapp.local","password":"DemoPass123!"}'

# 2. Health check
curl http://localhost:8000/gateway/health/?module=/health.php

# 3. Obtain token
TOKEN=$(curl -s -X POST http://localhost:8000/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"demo_user1","password":"DemoPass123!"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access'])")

# 4. Upload file
curl -X POST http://localhost:8000/gateway/transport/ \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@sample_demo.zip"

# 5. Search users
curl -X POST http://localhost:8000/gateway/user/find/?offset=0 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"username":"demo_user1"}'
```

---

## Error Codes Summary

| Status | Meaning |
|--------|---------|
| 200 | Success (response body indicates OK/ERR for health check) |
| 400 | Validation error (missing/invalid fields) |
| 401 | Unauthorized (missing/invalid/expired JWT) |
| 403 | Forbidden (insufficient permissions) |
| 500 | Internal server error |
