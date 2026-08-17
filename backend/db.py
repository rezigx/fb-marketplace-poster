"""
Database layer for the license/subscription backend.

Storage: SQLite (file-based, no external DB server).
Tables:
  - customers      (id, name, phone, license_key, created_at)
  - subscriptions  (id, customer_id, status, started_at, expires_at)
"""

import os
import sqlite3
import secrets
import datetime

DB_PATH = os.environ.get("DB_PATH", os.path.join(os.path.dirname(__file__), "data.db"))


def _now() -> str:
    return datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT DEFAULT '',
            license_key TEXT UNIQUE NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'inactive',  -- 'active' | 'inactive' | 'expired'
            started_at TEXT DEFAULT NULL,
            expires_at TEXT DEFAULT NULL,
            FOREIGN KEY(customer_id) REFERENCES customers(id)
        );
        """
    )
    conn.commit()
    conn.close()


def generate_license_key() -> str:
    """Generate a human-friendly license key like XXXX-XXXX-XXXX-XXXX."""
    raw = secrets.token_hex(8).upper()  # 16 hex chars
    return "-".join(raw[i : i + 4] for i in range(0, 16, 4))


def create_customer(name: str, phone: str = "", duration_days: int = 30):
    """Create a customer + an inactive subscription (inactive until admin activates)."""
    conn = get_conn()
    key = generate_license_key()
    while conn.execute("SELECT 1 FROM customers WHERE license_key = ?", (key,)).fetchone():
        key = generate_license_key()
    conn.execute(
        "INSERT INTO customers (name, phone, license_key, created_at) VALUES (?, ?, ?, ?)",
        (name, phone, key, _now()),
    )
    customer_id = conn.execute(
        "SELECT id FROM customers WHERE license_key = ?", (key,)
    ).fetchone()["id"]
    conn.execute(
        "INSERT INTO subscriptions (customer_id, status) VALUES (?, 'inactive')",
        (customer_id,),
    )
    conn.commit()
    conn.close()
    return {"id": customer_id, "name": name, "phone": phone, "license_key": key}


def activate_customer(customer_id: int, duration_days: int = 30):
    """Activate (or renew) a customer's subscription for `duration_days` from now."""
    conn = get_conn()
    now = datetime.datetime.utcnow()
    expires = now + datetime.timedelta(days=duration_days)
    conn.execute(
        """
        UPDATE subscriptions
        SET status = 'active',
            started_at = ?,
            expires_at = ?
        WHERE customer_id = ?
        """,
        (_now(), expires.strftime("%Y-%m-%d %H:%M:%S"), customer_id),
    )
    conn.commit()
    conn.close()
    return {"customer_id": customer_id, "expires_at": expires.strftime("%Y-%m-%d %H:%M:%S")}


def deactivate_customer(customer_id: int):
    conn = get_conn()
    conn.execute(
        "UPDATE subscriptions SET status = 'inactive', expires_at = NULL WHERE customer_id = ?",
        (customer_id,),
    )
    conn.commit()
    conn.close()
    return {"customer_id": customer_id, "status": "inactive"}


def check_license(license_key: str):
    """Return the license status for a given key. Used by the desktop app.

    Returns dict:
      { valid: bool, status: 'active'|'inactive'|'expired'|'not_found',
        expires_at: str|None, name: str|None }
    """
    conn = get_conn()
    row = conn.execute(
        """
        SELECT c.name, s.status, s.expires_at
        FROM customers c
        LEFT JOIN subscriptions s ON s.customer_id = c.id
        WHERE c.license_key = ?
        """,
        (license_key,),
    ).fetchone()
    conn.close()

    if row is None:
        return {"valid": False, "status": "not_found", "expires_at": None, "name": None}

    status = row["status"]
    expires_at = row["expires_at"]
    name = row["name"]

    # Auto-expire if past expiry
    if status == "active" and expires_at:
        exp_dt = datetime.datetime.strptime(expires_at, "%Y-%m-%d %H:%M:%S")
        if datetime.datetime.utcnow() > exp_dt:
            status = "expired"

    return {
        "valid": status == "active",
        "status": status,
        "expires_at": expires_at,
        "name": name,
    }


def list_customers():
    conn = get_conn()
    rows = conn.execute(
        """
        SELECT c.id, c.name, c.phone, c.license_key, c.created_at,
               s.status, s.started_at, s.expires_at
        FROM customers c
        LEFT JOIN subscriptions s ON s.customer_id = c.id
        ORDER BY c.id DESC
        """
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
