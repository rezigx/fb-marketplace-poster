"""
Application settings: loaded from / saved to a local JSON file next to the app.
"""

import json
import os

APP_DIR = os.path.dirname(os.path.abspath(__file__))
SETTINGS_FILE = os.path.join(os.path.dirname(APP_DIR), "settings.json")

DEFAULTS = {
    "whatsapp_number": "+213795031350",   # seed — customer changes it
    "license_key": "",
    "api_base_url": "https://your-backend.onrender.com",  # set after deploy
    "selected_wilayas": [],               # empty = all 58
    "daily_post_cap": 30,                 # daily safety cap
    "min_delay_sec": 30,
    "max_delay_sec": 90,
}


def load_settings() -> dict:
    data = dict(DEFAULTS)
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data.update(json.load(f))
        except Exception:
            pass
    return data


def save_settings(settings: dict):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)


def get(key: str):
    return load_settings().get(key, DEFAULTS.get(key))


def set_value(key: str, value):
    s = load_settings()
    s[key] = value
    save_settings(s)
