# Frontend Final Handoff Note

## 1. Overview

| Item | Detail |
|------|--------|
| **Project** | SuperApp Demo Phase — Frontend |
| **Date** | 2025-06-01 |
| **Status** | Ready for demo integration |
| **Frontend URL** | `http://localhost:3000` |
| **Backend URL** | `http://localhost:8000` |

---

## 2. Stack

| Layer | Technology |
|-------|-----------|
| Framework | Vite + React 19 + TypeScript |
| Routing | React Router DOM v7 |
| State | Zustand (persist middleware) |
| Data Fetching | TanStack Query |
| Forms | React Hook Form |
| Styling | Tailwind CSS 4 (Vite plugin) |
| UI Components | shadcn/ui-inspired (custom-built: Button, Input, Label, Card, Badge, Alert, Tabs, Separator) |
| Icons | Lucide React |
| Fonts | Instrument Sans (display) + JetBrains Mono (monospace) |

---

## 3. Screens Implemented

| Screen | Route | Auth | Description |
|--------|-------|------|-------------|
| Landing | `/` | No | Hero, feature grid, terminal CTA, nav |
| Login | `/login` | No | Credentials form, demo credentials hint |
| Register | `/register` | No | Full registration with password confirmation, auto-login on success |
| Dashboard | `/dashboard` | Yes | Tabbed console: File Upload, Health Check, User Search |

---

## 4. API Integration Map

| API Endpoint | Frontend Usage | Screen(s) |
|-------------|----------------|-----------|
| `POST /gateway/user/` | Registration form submit | Register |
| `POST /auth/token/` | Login, auto-login after register | Login, Register, Auth Store |
| `POST /auth/refresh-token/` | Defined in API layer | Auth Store (available) |
| `POST /gateway/transport/` | File upload with drag-and-drop | Dashboard (Upload tab) |
| `GET /gateway/health/` | Service health probe | Dashboard (Health tab) |
| `POST /gateway/user/find/` | Username/email search | Dashboard (Search tab) |

---

## 5. API Contract Gaps & Issues

### G5 — No explicit user profile endpoint
The API has no `GET /gateway/user/me/` or equivalent. The frontend infers the current user from the login username. If the backend adds a profile endpoint, the auth store should be updated to fetch it on login.

### G6 — Health check returns plain text, not JSON
The health endpoint returns `"OK"` or `"ERR"` as plain strings. The frontend handles this correctly, but consumers expecting JSON will need adjustment.

### G7 — No file upload progress feedback
The `POST /gateway/transport/` endpoint is synchronous with a 2-second timeout. No streaming or chunked upload is available. For files near the timeout boundary, the UI shows a spinner with no progress percentage.

### G8 — No pagination controls on user search
The `POST /gateway/user/find/` endpoint accepts an `offset` query parameter, but the response does not include total count or next-page cursor. The dashboard shows results without pagination UI.

### G9 — No logout / token invalidation endpoint
The frontend clears the token locally on sign-out, but there is no backend endpoint to blacklist or revoke the refresh token. A logged-out user could still use a valid refresh token until it expires.

### G10 — CSRF / CORS not configured for production
The Vite dev server proxies API calls to `localhost:8000`. In production, the Django backend would need CORS middleware configured to allow the frontend origin.

---

## 6. Known Limitations (inherited from backend)

| # | Limitation | Frontend Impact |
|---|-----------|----------------|
| L2 | SECRET_KEY randomizes on restart | JWT tokens invalidated; user must re-login |
| L3 | ZIP validation checks names only | UI shows allowed extensions but cannot guarantee content safety |
| L7 | 2-second upload timeout | UI warns "max ~1MB" but cannot detect timeout before it happens |

---

## 7. How to Run

```bash
# Terminal 1 — Start backend
cd demo/backend
docker compose up --build
docker compose exec app1 python manage.py seed_demo

# Terminal 2 — Start frontend
cd demo/frontend
npm run dev
```

Open `http://localhost:3000` in a browser.

---

## 8. Design System

**Aesthetic**: Industrial / utilitarian dark mode

| Token | Value | Purpose |
|-------|-------|---------|
| Background | `hsl(220 15% 9%)` | Deep slate |
| Foreground | `hsl(215 15% 88%)` | Cool light gray |
| Primary | `hsl(170 35% 42%)` | Oxidized teal |
| Accent | `hsl(38 75% 55%)` | Amber highlight |
| Destructive | `hsl(0 65% 50%)` | Alert red |
| Card | `hsl(220 15% 12%)` | Elevated surface |
| Border | `hsl(220 12% 22%)` | Subtle divider |

**Typography**: Instrument Sans (400–700) for UI text, JetBrains Mono for code/terminal blocks.

---

**Handoff complete.** Frontend is ready for demo integration with the backend.
