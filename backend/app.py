"""
License / subscription backend API.

Endpoints:
  POST /api/register              -> create customer + license key (public)
  GET  /api/license?key=...       -> check license (called by the desktop app)
  POST /api/activate              -> admin: activate/renew a customer
  POST /api/deactivate            -> admin: deactivate a customer
  GET  /api/customers             -> admin: list all customers
  GET  /api/health                -> uptime check

Admin protection: an ADMIN_TOKEN (set via env var). All admin routes require
the `Authorization: Bearer <ADMIN_TOKEN>` header OR `?token=...` for the panel.
"""

import os
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
import pathlib

import db

app = FastAPI(title="FB Poster License Backend")
db.init_db()

ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "change-me-admin-token")
ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
ADMIN_PASS = os.environ.get("ADMIN_PASS", "admin123")


# ---------- Pydantic models ----------
class RegisterRequest(BaseModel):
    name: str
    phone: str = ""
    duration_days: int = 30


class ActivateRequest(BaseModel):
    customer_id: int
    duration_days: int = 30


class DeactivateRequest(BaseModel):
    customer_id: int


# ---------- Auth helpers ----------
def _require_admin(authorization: Optional[str] = Header(None)):
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
    if token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return True


# ---------- Public endpoints ----------
@app.post("/api/register")
def register(req: RegisterRequest):
    if not req.name or not req.name.strip():
        raise HTTPException(status_code=400, detail="name is required")
    customer = db.create_customer(req.name.strip(), req.phone.strip(), req.duration_days)
    return JSONResponse(customer)


@app.get("/api/license")
def license_check(key: str = ""):
    result = db.check_license(key.strip())
    # Never leak the full customer list; just the status for this key.
    return JSONResponse(result)


@app.get("/api/health")
def health():
    return {"status": "ok"}


# ---------- Admin endpoints ----------
@app.post("/api/activate", dependencies=[Depends(_require_admin)])
def activate(req: ActivateRequest):
    result = db.activate_customer(req.customer_id, req.duration_days)
    return JSONResponse(result)


@app.post("/api/deactivate", dependencies=[Depends(_require_admin)])
def deactivate(req: DeactivateRequest):
    result = db.deactivate_customer(req.customer_id)
    return JSONResponse(result)


@app.get("/api/customers", dependencies=[Depends(_require_admin)])
def customers():
    return JSONResponse(db.list_customers())


# ---------- Admin panel (plain HTML, token passed via ?token=) ----------
ADMIN_PANEL_HTML = pathlib.Path(os.path.join(os.path.dirname(__file__), "admin_panel", "index.html"))

@app.get("/admin", response_class=HTMLResponse)
def admin_panel():
    return ADMIN_PANEL_HTML.read_text(encoding="utf-8")
