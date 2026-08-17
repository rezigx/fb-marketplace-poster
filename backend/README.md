# Backend — deploy & run instructions

A FastAPI + SQLite service that handles license validation and provides your admin panel.

## 1. Run locally (test)

```bash
cd backend
pip install -r requirements.txt
python -c "import db; db.init_db()"
ADMIN_TOKEN="super-secret-token" uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

Then open:
- Admin panel: http://localhost:8000/admin  (paste your `ADMIN_TOKEN`)
- Health check: http://localhost:8000/api/health

## 2. Environment variables

| Var | Purpose | Default |
|---|---|---|
| `ADMIN_TOKEN` | Protects all `/api/*` admin routes + panel | `change-me-admin-token` |
| `DB_PATH` | SQLite file location | `backend/data.db` |

> **Set a strong `ADMIN_TOKEN` in production.** This is your master key.

## 3. Deploy (free/cheap options)

### Option A — Render (recommended, easy)
1. Push this `backend/` folder to a GitHub repo.
2. On render.com: New → Web Service → connect repo.
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn app:app --host 0.0.0.0 --port $PORT`
5. Add env var `ADMIN_TOKEN`.
6. Free tier sleeps after inactivity — acceptable for a license check (first call may be slow).

### Option B — Railway
Similar to Render; add `backend/` as root, set start command and `ADMIN_TOKEN`.

## 4. API reference

| Method | Path | Auth | Body | Description |
|---|---|---|---|---|
| POST | `/api/register` | none | `{name, phone?, duration_days?}` | Create customer + license key |
| GET  | `/api/license?key=...` | none | — | Check license status |
| POST | `/api/activate` | Bearer ADMIN_TOKEN | `{customer_id, duration_days?}` | Activate/renew |
| POST | `/api/deactivate` | Bearer ADMIN_TOKEN | `{customer_id}` | Deactivate |
| GET  | `/api/customers` | Bearer ADMIN_TOKEN | — | List all customers |
| GET  | `/api/health` | none | — | Uptime check |

## 5. Note on `license_check` response shape

The desktop app expects:
```json
{ "valid": true, "status": "active", "expires_at": "2026-09-15 12:00:00", "name": "..." }
```
`status` is one of: `active`, `inactive`, `expired`, `not_found`.
