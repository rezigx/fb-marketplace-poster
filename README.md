# FB Marketplace Multi-State Poster

A sellable Windows desktop app that posts a product to Facebook Marketplace across **all 58 Algerian wilayas** at once, driven by Playwright browser automation, with leads routed to a single WhatsApp number. Sold as a **monthly subscription** (CCP / BaridiMob payment → manual activation in an admin panel).

> ⚠️ **Honest disclaimer:** Automating Facebook Marketplace is gray-area against Facebook's Terms of Service. The app uses human-like randomized delays, daily caps, and per-listing wording variation to minimize ban risk, but that risk is inherent to the product. Facebook's "Create listing" flow also changes frequently, so automation selectors may need periodic tuning.

---

## Architecture

```
Desktop App (PySide6, .exe)  ──HTTPS──▶  Cloud Backend (FastAPI + SQLite)
        │                                   license / subscription check
        │                                   + your admin panel
        ▼
Facebook Marketplace (Playwright browser automation, saved session)
```

### Backend (`backend/`)
- `POST /api/register` — create customer + license key
- `POST /api/activate` / `POST /api/deactivate` — admin (token-protected)
- `GET  /api/license?key=...` — license status (called by the app)
- `GET  /api/health`
- Admin panel (`/admin`) — web UI to view/activate/deactivate customers

### Desktop app (`desktop/`)
- **Steam-style glassmorphism UI** (`main_qt.py`, PySide6) + Tkinter fallback (`main.py`)
- **Product builder** — images + title/desc/price/category (no Google Sheet needed)
- **License gate** — blocks posting when subscription is inactive/expired
- **58 wilayas** (`facebook/wilayas.py`) with Arabic names
- **Facebook automation** (`facebook/automation.py`, Playwright)
- WhatsApp number auto-appended to every listing

---

## Folder structure

```
fb-marketplace-poster/
├── README.md
├── PLAN.md
├── .gitignore
├── backend/
│   ├── app.py
│   ├── db.py
│   ├── requirements.txt
│   ├── README.md
│   └── admin_panel/index.html
├── desktop/
│   ├── main_qt.py
│   ├── main.py
│   ├── settings.py
│   ├── license.py
│   ├── requirements.txt
│   └── facebook/
│       ├── automation.py
│       ├── wilayas.py
│       └── __init__.py
├── docs/USER_GUIDE.md
└── packaging/build.md
```

---

## Quick start (developer)

### Backend
```bash
cd backend
pip install -r requirements.txt
ADMIN_TOKEN="super-secret-token" uvicorn app:app --reload --port 8000
# admin panel: http://localhost:8000/admin
```

### Desktop app
```bash
cd desktop
pip install -r requirements.txt
python main_qt.py
```

### Build .exe
See `packaging/build.md`.

---

## Key design decisions

| Decision | Choice | Why |
|---|---|---|
| Facebook access | Playwright browser automation (real login, saved session) | Only viable path for personal marketplace bulk-posting |
| Product data | Built-in editor (no Google Sheet) | Customer drops images + types fields |
| WhatsApp | Configurable number, auto-appended | Each buyer uses their own number |
| Monetization | Monthly subscription, backend-validated | Recurring revenue, can't be bypassed by editing the .exe |
| Payment | CCP / BaridiMob, manual activation | No auto-webhook in Algeria |
| Safety | Randomized delays, daily caps, wording variation | Minimize ban risk |

---

## Roadmap / status

See `PLAN.md`. The backend is built and tested end-to-end. Facebook selectors are best-effort and must be validated against the live UI (Stage 4). Backend still needs deployment (Render/Railway free tier).
