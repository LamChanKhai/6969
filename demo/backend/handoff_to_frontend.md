# Backend → Frontend Handoff Note

## 1. Overview

| Item | Detail |
|------|--------|
| **Project** | SuperApp Demo Phase |
| **Date** | 2025-06-01 |
| **Status** | Backend ready for frontend integration |
| **Base URL** | `http://localhost:8000` |

---

## 2. Running the Demo Environment

```bash
# Start both services
docker compose up --build

# Seed demo data (run inside app1 container)
docker compose exec app1 python manage.py seed_demo

# Stop environment
docker compose down
```

Both services start automatically. App1 (Django/uWSGI) listens on port 8000. App2 (PHP/Apache) is internal-only, reachable from App1 via `http://app2`.

---

## 3. Available API Endpoints

See `API_CONTRACT.md` for full endpoint documentation with schemas, status codes, and curl examples.

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/gateway/user/` | POST | No | Register user |
| `/auth/token/` | POST | No | Obtain JWT token |
| `/auth/refresh-token/` | POST | No | Refresh JWT token |
| `/gateway/transport/` | POST | Yes | Upload ZIP file |
| `/gateway/health/` | GET | No | Health check |
| `/gateway/user/find/` | POST | Yes | Search users |

---

## 4. Pre-seeded Demo Users

Run `python manage.py seed_demo` inside the app1 container to create:

| Username | Password |
|----------|----------|
| demo_user1 | DemoPass123! |
| demo_user2 | DemoPass456! |
| demo_user3 | DemoPass789! |

A sample ZIP file (`sample_demo.zip`) is also generated in the working directory.

---

## 5. Known Limitations & Temporary Workarounds

| # | Limitation | Impact | Workaround |
|---|-----------|--------|------------|
| L1 | SQLite database is ephemeral (no persistent volume in original design) | Data lost on container restart | Added `db-data` named volume in docker-compose.yaml for persistence during demo |
| L2 | Django SECRET_KEY is randomized on every container restart | JWT tokens become invalid after restart | Re-obtain token after each restart. Acceptable for demo. |
| L3 | File validation only checks ZIP entry names, not actual file content/type | A crafted ZIP with renamed entries could bypass validation | Noted for future security review. Demo uses pre-validated sample files. |
| L4 | App2 is not accessible from outside Docker network | Cannot directly test App2 endpoints from host | Use App1's health check endpoint as proxy: `GET /gateway/health/?module=/health.php` |
| L5 | User search (`/gateway/user/find/`) accepts arbitrary filter kwargs | Potential for unexpected filter behavior | For demo, use `username` and `email` filters only |
| L6 | No rate limiting on any endpoint | API can be called unlimited times | Not applicable for demo scope |
| L7 | File upload timeout is 2 seconds (hardcoded in utils.py) | Large files may timeout | Demo uses small sample ZIP (< 1MB) |

---

## 6. File Upload Constraints

- **Format**: ZIP file only
- **Allowed extensions inside ZIP**: `.txt`, `.docx`, `.png`, `.jpg`, `.jpeg`
- **Max practical size**: ~1MB (due to 2-second timeout)
- **Content-Type**: `multipart/form-data` with field name `file`

---

## 7. Authentication Requirements

- All protected endpoints require `Authorization: Bearer <access_token>` header
- Access tokens expire per default SimpleJWT settings (5 minutes)
- Use refresh token endpoint to obtain new access tokens
- Tokens are invalidated on container restart (random SECRET_KEY)

---

## 8. Test Coverage

Unit and integration tests are located at `app1/src/gateway/tests/test_demo_flows.py`.

To run tests:

```bash
docker compose exec app1 python manage.py test gateway.tests
```

Test coverage includes:
- File validation utility functions
- Health check utility functions
- File transport utility functions
- User registration API
- JWT token endpoints
- Health check endpoint
- File upload endpoint
- User search endpoint

---

## 9. Project Structure

```
demo/backend/
├── docker-compose.yaml        # Service orchestration
├── .dockerignore              # Docker build exclusions
├── API_CONTRACT.md            # Full API documentation
├── handoff_to_frontend.md     # This file
├── app1/                      # Django gateway service
│   ├── Dockerfile
│   ├── entrypoint.sh
│   └── src/
│       ├── manage.py
│       ├── requirements.txt
│       ├── uwsgi.ini
│       ├── superapp/          # Django project config
│       └── gateway/           # Main application
│           ├── models.py
│           ├── views.py
│           ├── serializers.py
│           ├── urls.py
│           ├── utils.py
│           ├── tests/
│           │   └── test_demo_flows.py
│           ├── management/
│           │   └── commands/
│           │       └── seed_demo.py
│           └── migrations/
└── app2/                      # PHP storage service
    ├── Dockerfile
    ├── flag.txt
    └── src/
        ├── storage.php
        ├── health.php
        └── vendor/
```

---

## 10. Next Steps for Frontend

1. Build UI around the 6 API endpoints documented in `API_CONTRACT.md`
2. Implement JWT token management (login → store token → attach to requests → refresh)
3. Create file upload component with ZIP format validation
4. Display health check status
5. Build user registration and search forms
6. Use pre-seeded demo users for initial testing

---

**Handoff complete.** Backend is ready for frontend integration.
