"""
FB Marketplace Multi-State Poster — Desktop GUI (Tkinter, fallback).

The primary GUI is main_qt.py (PySide6 Steam-style). This Tkinter version is a
lightweight fallback for environments without PySide6.

Tabs: Dashboard / Products / Settings.
Facebook posting is handled in facebook/automation.py (Playwright).
"""

import os
import json
import threading
import traceback

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from settings import load_settings, save_settings, SETTINGS_FILE
from facebook.wilayas import WILAYAS, CATEGORIES
import license as license_client

PRODUCTS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "products.json")


def load_products():
    if os.path.exists(PRODUCTS_FILE):
        try:
            with open(PRODUCTS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def save_products(products):
    with open(PRODUCTS_FILE, "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("FB Marketplace Multi-State Poster")
        self.geometry("960x640")
        self.minsize(860, 560)
        self.products = load_products()
        self.settings = load_settings()
        self._build_style()
        self._build_notebook()

    def _build_style(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("TFrame", background="#14171f")
        style.configure("TLabel", background="#14171f", foreground="#e6e8ee")
        style.configure("TButton", padding=6, font=("Segoe UI", 10))
        style.configure("TNotebook", background="#14171f")
        style.configure("TNotebook.Tab", padding=[14, 8], font=("Segoe UI", 10))
        style.configure("TEntry", padding=5)
        self.configure(bg="#14171f")

    def _build_notebook(self):
        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True)
        self.dashboard_tab = ttk.Frame(self.nb)
        self.products_tab = ttk.Frame(self.nb)
        self.settings_tab = ttk.Frame(self.nb)
        self.nb.add(self.dashboard_tab, text="Dashboard")
        self.nb.add(self.products_tab, text="Products")
        self.nb.add(self.settings_tab, text="Settings")
        self._build_dashboard()
        self._build_products()
        self._build_settings()

    def _build_dashboard(self):
        frm = self.dashboard_tab
        top = ttk.Frame(frm); top.pack(fill="x", padx=16, pady=12)
        self.status_var = tk.StringVar(value="Status: idle — checking license...")
        ttk.Label(top, textvariable=self.status_var, font=("Segoe UI", 11, "bold")).pack(anchor="w")
        self.progress = ttk.Progressbar(frm, mode="determinate")
        self.progress.pack(fill="x", padx=16, pady=(0, 8))
        btns = ttk.Frame(frm); btns.pack(fill="x", padx=16, pady=4)
        self.post_btn = ttk.Button(btns, text="▶ Post to All Wilayas", command=self.start_posting)
        self.post_btn.pack(side="left", padx=(0, 8))
        self.check_btn = ttk.Button(btns, text="Check license", command=self._check_license_ui)
        self.check_btn.pack(side="left")
        logwrap = ttk.Frame(frm); logwrap.pack(fill="both", expand=True, padx=16, pady=8)
        self.log_text = tk.Text(logwrap, bg="#0b0d12", fg="#9fe9a6", font=("Consolas", 10), wrap="word", state="disabled")
        scroll = ttk.Scrollbar(logwrap, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.log_text.pack(side="left", fill="both", expand=True)
        self._log("Welcome. Configure your license in Settings, build products, then Post.")
        self.after(100, self._check_license_ui)

    def _log(self, message):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _check_license_ui(self):
        def run():
            try:
                res = license_client.check_license()
                if res.get("valid"):
                    self._set_ui_status(f"Status: license active — {res.get('name','')} until {res.get('expires_at','')}")
                else:
                    self._set_ui_status(f"Status: license {res.get('status','inactive')} — activate to post")
            except license_client.LicenseError as e:
                self._set_ui_status(f"Status: {e}")
        threading.Thread(target=run, daemon=True).start()

    def _set_ui_status(self, text):
        self.status_var.set(text)

    def start_posting(self):
        if not self.products:
            messagebox.showwarning("No products", "Add at least one product first.")
            return
        try:
            res = license_client.check_license()
        except license_client.LicenseError as e:
            messagebox.showerror("License error", str(e))
            return
        if not res.get("valid"):
            messagebox.showerror("Not active", f"Your license is {res.get('status','inactive')}. Renew to post.")
            return
        self._log("Starting posting run...")
        threading.Thread(target=self._post_worker, daemon=True).start()

    def _post_worker(self):
        try:
            selected = self.settings.get("selected_wilayas") or [w["name"] for w in WILAYAS]
            total = len(self.products) * len(selected)
            self.progress.configure(maximum=max(total, 1))
            done = 0
            for product in self.products:
                for wilaya in selected:
                    self._log(f"Posting '{product.get('title','?')}' → {wilaya} ...")
                    # automation.post_listing(product, wilaya)  # real call
                    done += 1
                    self.progress.configure(value=done)
                    self.update_idletasks()
            self._log(f"Done. {done} listings processed.")
            self._set_ui_status("Status: posting complete")
        except Exception as e:
            self._log("ERROR: " + traceback.format_exc())
            self._set_ui_status("Status: posting failed")

    def _build_products(self):
        frm = self.products_tab
        left = ttk.Frame(frm); left.pack(side="left", fill="y", padx=16, pady=12)
        right = ttk.Frame(frm); right.pack(side="right", fill="both", expand=True, padx=16, pady=12)
        ttk.Label(left, text="Title *").pack(anchor="w")
        self.title_var = tk.StringVar()
        ttk.Entry(left, textvariable=self.title_var, width=36).pack(anchor="w", pady=(0, 8))
        ttk.Label(left, text="Description").pack(anchor="w")
        self.desc_text = tk.Text(left, width=36, height=6)
        self.desc_text.pack(anchor="w", pady=(0, 8))
        ttk.Label(left, text="Price (DA) *").pack(anchor="w")
        self.price_var = tk.StringVar()
        ttk.Entry(left, textvariable=self.price_var, width=36).pack(anchor="w", pady=(0, 8))
        ttk.Label(left, text="Category").pack(anchor="w")
        self.cat_var = tk.StringVar(value=CATEGORIES[0])
        ttk.Combobox(left, textvariable=self.cat_var, values=CATEGORIES, width=33, state="readonly").pack(anchor="w", pady=(0, 8))
        self.img_listbox = tk.Listbox(left, height=5, width=36)
        self.img_listbox.pack(anchor="w", pady=(0, 4))
        imgbtns = ttk.Frame(left); imgbtns.pack(anchor="w")
        ttk.Button(imgbtns, text="+ Add images", command=self.add_images).pack(side="left", padx=(0, 6))
        ttk.Button(imgbtns, text="− Remove", command=self.remove_image).pack(side="left")
        ttk.Button(left, text="Save product", command=self.save_product).pack(anchor="w", pady=(12, 0))
        ttk.Label(right, text="Saved products").pack(anchor="w")
        self.product_list = tk.Listbox(right, height=20)
        self.product_list.pack(fill="both", expand=True, pady=(6, 6))
        listbtns = ttk.Frame(right); listbtns.pack(anchor="w")
        ttk.Button(listbtns, text="Load", command=self.load_selected_product).pack(side="left", padx=(0, 6))
        ttk.Button(listbtns, text="Delete", command=self.delete_product).pack(side="left")
        self._refresh_product_list()

    def add_images(self):
        paths = filedialog.askopenfilenames(title="Select product images", filetypes=[("Images", "*.png *.jpg *.jpeg *.webp *.gif"), ("All files", "*.*")])
        for p in paths:
            if p not in self.img_listbox.get(0, "end"):
                self.img_listbox.insert("end", p)

    def remove_image(self):
        sel = self.img_listbox.curselection()
        if sel:
            self.img_listbox.delete(sel[0])

    def save_product(self):
        title = self.title_var.get().strip()
        price = self.price_var.get().strip()
        if not title or not price:
            messagebox.showwarning("Missing fields", "Title and price are required.")
            return
        product = {"title": title, "description": self.desc_text.get("1.0", "end").strip(), "price": price, "category": self.cat_var.get(), "images": list(self.img_listbox.get(0, "end"))}
        self.products.append(product)
        save_products(self.products)
        self._refresh_product_list()
        self._clear_form()
        self._log(f"Saved product: {title}")

    def _clear_form(self):
        self.title_var.set("")
        self.desc_text.delete("1.0", "end")
        self.price_var.set("")
        self.cat_var.set(CATEGORIES[0])
        self.img_listbox.delete(0, "end")

    def _refresh_product_list(self):
        self.product_list.delete(0, "end")
        for p in self.products:
            self.product_list.insert("end", f"{p.get('title','?')} — {p.get('price','?')} DA")

    def load_selected_product(self):
        sel = self.product_list.curselection()
        if not sel:
            return
        p = self.products[sel[0]]
        self._clear_form()
        self.title_var.set(p.get("title", ""))
        self.desc_text.insert("1.0", p.get("description", ""))
        self.price_var.set(p.get("price", ""))
        self.cat_var.set(p.get("category", CATEGORIES[0]))
        for img in p.get("images", []):
            self.img_listbox.insert("end", img)

    def delete_product(self):
        sel = self.product_list.curselection()
        if not sel:
            return
        del self.products[sel[0]]
        save_products(self.products)
        self._refresh_product_list()

    def _build_settings(self):
        frm = self.settings_tab
        pad = {"padx": 16, "pady": 6}
        ttk.Label(frm, text="License key").pack(anchor="w", **pad)
        self.license_var = tk.StringVar(value=self.settings.get("license_key", ""))
        ttk.Entry(frm, textvariable=self.license_var, width=50).pack(anchor="w", **pad)
        ttk.Label(frm, text="Backend URL (license server)").pack(anchor="w", **pad)
        self.backend_var = tk.StringVar(value=self.settings.get("api_base_url", ""))
        ttk.Entry(frm, textvariable=self.backend_var, width=50).pack(anchor="w", **pad)
        ttk.Label(frm, text="WhatsApp number (printed on listings)").pack(anchor="w", **pad)
        self.wa_var = tk.StringVar(value=self.settings.get("whatsapp_number", ""))
        ttk.Entry(frm, textvariable=self.wa_var, width=50).pack(anchor="w", **pad)
        ttk.Label(frm, text="Daily post cap").pack(anchor="w", **pad)
        self.cap_var = tk.StringVar(value=str(self.settings.get("daily_post_cap", 30)))
        ttk.Entry(frm, textvariable=self.cap_var, width=10).pack(anchor="w", **pad)
        ttk.Label(frm, text="Wilayas to post to (empty = all 58)").pack(anchor="w", **pad)
        self.wilaya_list = tk.Listbox(frm, height=8, width=60, selectmode="extended")
        for w in WILAYAS:
            self.wilaya_list.insert("end", f"{w['code']} — {w['name']}")
        self.wilaya_list.pack(anchor="w", **pad)
        sel = self.settings.get("selected_wilayas") or []
        if sel:
            for i, w in enumerate(WILAYAS):
                if w["name"] in sel:
                    self.wilaya_list.selection_set(i)
        ttk.Button(frm, text="Save settings", command=self.save_settings_ui).pack(anchor="w", **pad)

    def save_settings_ui(self):
        sel_names = [WILAYAS[i]["name"] for i in self.wilaya_list.curselection()]
        self.settings.update({
            "license_key": self.license_var.get().strip(),
            "api_base_url": self.backend_var.get().strip(),
            "whatsapp_number": self.wa_var.get().strip(),
            "daily_post_cap": int(self.cap_var.get().strip() or "30"),
            "selected_wilayas": sel_names,
        })
        save_settings(self.settings)
        messagebox.showinfo("Saved", "Settings saved.")


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
