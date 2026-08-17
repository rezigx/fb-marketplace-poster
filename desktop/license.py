"""
License / subscription client — validates the user's license against the backend.

The app gates posting behind an active subscription. On expiry the user must
renew (pay via CCP/BaridiMob → admin activates them).
"""

import json
import urllib.request
import urllib.error
import urllib.parse

from settings import load_settings, save_settings


class LicenseError(Exception):
    pass


def _get(url: str, timeout: int = 15) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "FBPoster/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def check_license(license_key: str = None) -> dict:
    """Query the backend for the license status. Returns the backend JSON.

    Raises LicenseError on network failure (app should treat as "can't verify",
    not automatically "invalid" — offline tolerance is configurable).
    """
    s = load_settings()
    key = (license_key or s.get("license_key", "")).strip()
    base = (s.get("api_base_url") or "").rstrip("/")

    if not key:
        return {"valid": False, "status": "not_found", "expires_at": None, "name": None}
    if not base:
        raise LicenseError("Backend URL not configured")

    url = f"{base}/api/license?key={urllib.parse.quote(key)}"
    try:
        return _get(url)
    except urllib.error.HTTPError as e:
        raise LicenseError(f"License server error {e.code}")
    except Exception as e:
        raise LicenseError(f"Cannot reach license server: {e}")


def is_active(result: dict) -> bool:
    return bool(result.get("valid"))
