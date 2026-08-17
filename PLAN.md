# Build Plan — FB Marketplace Multi-State Poster

Build order, staged so we have working pieces at every milestone.

## Stage 0 — Foundation ✅
- [x] Workspace + README + this plan
- [x] Tech stack locked: PySide6 GUI, Playwright automation, FastAPI+SQLite backend, PyInstaller packaging

## Stage 1 — Backend (license + subscription) ✅
- [x] SQLite schema (customers + subscriptions)
- [x] FastAPI endpoints (register / activate / deactivate / license / customers / health)
- [x] Admin panel (web UI)
- [x] Tested end-to-end (register → activate → check → auth-rejection → unknown-key)
- [ ] **Deploy** to Render/Railway (free tier)

## Stage 2 — Desktop app core ✅
- [x] GUI (3 tabs: Dashboard / Products / Settings)
- [x] Product builder (images + title/desc/price/category)
- [x] Settings (WhatsApp number, wilaya selection, license key, backend URL, caps)
- [x] Local persistence (JSON)
- [x] Steam-style glassmorphism UI (PySide6) + Tkinter fallback

## Stage 3 — License integration ✅
- [x] `license.py` client — call backend, gate posting on active subscription
- [x] Wired into launch + posting flow

## Stage 4 — Facebook automation (the hard part) ⚠️
- [x] `wilayas.py` — 58 wilayas + Arabic names
- [x] `automation.py` — Playwright: saved session, delays, wording variation
- [ ] **Validate selectors against live Facebook "Create listing" UI**
- [ ] Wire `post_listing()` live (currently stubbed in the GUI)
- [ ] Live login test with a real account

## Stage 5 — Packaging + docs ✅
- [x] PyInstaller build instructions (`packaging/build.md`)
- [x] User guide (`docs/USER_GUIDE.md`)

## Stage 6 — Sell-ready extras
- [ ] Landing page + pricing
- [ ] License key generator flow
- [ ] (later) auto-update

---

## Open questions
1. Backend host (Render / Railway / Alwaysdata / PythonAnywhere)
2. Exact FB "Create listing" flow — inspect live during Stage 4
