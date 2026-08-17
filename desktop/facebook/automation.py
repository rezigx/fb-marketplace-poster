"""
Facebook Marketplace automation via Playwright.

Core flows:
  - ensure_logged_in(): opens a visible browser, logs in once, persists session
  - post_listing(product, wilaya, settings): creates a Marketplace listing

SAFETY: human-like randomized delays (30–90s) and slight wording variation
between listings to avoid spam detection. Daily caps enforced by the caller.

IMPORTANT / HONEST NOTE: Facebook's "Create listing" flow changes frequently
and Marketplace has no stable public automation API for personal accounts.
The selectors below are reasonable best-effort defaults and MUST be validated
against the live UI. Treat this file as a starting point to be tuned.
"""

import os
import random
import time

from playwright.sync_api import sync_playwright

# Where the saved Facebook login session lives.
SESSION_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fb_session.json")


def _human_delay(min_s=30, max_s=90):
    time.sleep(random.uniform(min_s, max_s))


def _variation(base: str, wilaya: str) -> str:
    """Slightly vary the title/description per wilaya so listings don't look identical."""
    prefix = random.choice([
        f"({wilaya}) {base}",
        f"{base} — {wilaya}",
        f"{base} | {wilaya}",
    ])
    return prefix


def _append_whatsapp(description: str, whatsapp: str) -> str:
    if whatsapp and whatsapp.strip():
        return f"{description}\n\n📞 Contact / WhatsApp: {whatsapp}".strip()
    return description


def ensure_logged_in(headless: bool = False):
    """Open a browser, log in if no saved session, and persist session state."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = (
            browser.new_context(storage_state=SESSION_FILE)
            if os.path.exists(SESSION_FILE)
            else browser.new_context()
        )
        page = context.new_page()
        page.goto("https://www.facebook.com")
        if "login" in page.url or "checkpoint" in page.url:
            print("Please log in to Facebook in the opened browser window...")
            page.wait_for_url("https://www.facebook.com/", timeout=600_000)
            context.storage_state(path=SESSION_FILE)
        browser.close()
    return True


def post_listing(product: dict, wilaya: dict, settings: dict, headless: bool = False):
    """Post a single Marketplace listing for one wilaya.

    product: {title, description, price, category, images:[...]}
    wilaya:  {code, name, name_ar}
    settings: dict with whatsapp_number, etc.
    """
    title = _variation(product.get("title", ""), wilaya["name"])
    description = _append_whatsapp(product.get("description", ""), settings.get("whatsapp_number", ""))
    price = product.get("price", "")
    images = product.get("images", [])

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = (
            browser.new_context(storage_state=SESSION_FILE)
            if os.path.exists(SESSION_FILE)
            else browser.new_context()
        )
        page = context.new_page()
        page.goto("https://www.facebook.com/marketplace/create/item")

        if "login" in page.url or "checkpoint" in page.url:
            print("Not logged in — run ensure_logged_in() first.")
            browser.close()
            return False

        # Title
        try:
            page.fill("input[aria-label*='title' i], textarea[aria-label*='title' i], input[aria-label*='Titre']", title)
        except Exception:
            try:
                page.locator("input").first.fill(title)
            except Exception as e:
                print("title fill failed:", e)

        # Price
        try:
            page.fill("input[aria-label*='price' i], input[aria-label*='Prix']", price)
        except Exception as e:
            print("price fill failed:", e)

        # Description
        try:
            page.fill("textarea[aria-label*='description' i], textarea[aria-label*='Description']", description)
        except Exception as e:
            print("description fill failed:", e)

        # Images
        if images:
            try:
                page.set_input_files("input[type='file']", images)
            except Exception as e:
                print("image upload failed:", e)

        # Location
        try:
            loc = page.locator("input[aria-label*='location' i], input[aria-label*='Localisation']")
            if loc.count():
                loc.first.fill(f"{wilaya['name']}, {wilaya['name_ar']}, Algeria")
        except Exception as e:
            print("location fill failed:", e)

        # Submit (Publish)
        try:
            page.click("div[aria-label*='Publish' i], div[aria-label*='Suivant' i], button:has-text('Publish')")
            _human_delay(settings.get("min_delay_sec", 30), settings.get("max_delay_sec", 90))
            browser.close()
            return True
        except Exception as e:
            print("publish click failed:", e)
            browser.close()
            return False
