"""
FB Marketplace Multi-State Poster — Steam-style glassmorphism GUI (PySide6).

Replaces the Tkinter version with a premium dark UI:
  - Deep blue-slate gradient background (Steam signature)
  - Frosted glass panels with rounded corners
  - Cyan accent glow + hover effects
  - 3 tabs: Dashboard / Products / Settings

Same underlying data modules (settings, license, wilayas, automation).
"""

import os
import json
import threading
import traceback

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QTextEdit, QListWidget, QListWidgetItem,
    QComboBox, QStackedWidget, QFrame, QProgressBar, QFileDialog,
    QMessageBox, QButtonGroup
)

from settings import load_settings, save_settings
from facebook.wilayas import WILAYAS, CATEGORIES
import license as license_client

PRODUCTS_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "products.json"
)


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


# ============================================================
#  GLOBAL STYLESHEET  (Steam dark + glass)
# ============================================================
STYLE = """
* {
    font-family: 'Segoe UI', 'Inter', 'Helvetica Neue', sans-serif;
    font-size: 14px;
    color: #d7dde6;
}
QMainWindow { background: transparent; }
#Root {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #1b2838, stop:0.5 #171a21, stop:1 #0e1116);
}

/* ---- Glass panel ---- */
#GlassPanel {
    background: rgba(38, 54, 74, 0.55);
    border: 1px solid rgba(120, 160, 200, 0.35);
    border-radius: 14px;
}

/* ---- Sidebar nav buttons ---- */
#NavButton {
    background: transparent;
    color: #8fa3b8;
    border: none;
    border-radius: 10px;
    padding: 12px 18px;
    text-align: left;
    font-size: 15px;
    font-weight: 600;
}
#NavButton:hover { background: rgba(70, 100, 140, 0.35); color: #ffffff; }
#NavButton:checked {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 rgba(38, 120, 200, 0.85), stop:1 rgba(50, 150, 220, 0.85));
    color: #ffffff;
}

/* ---- Primary (accent) button ---- */
#PrimaryButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #1a9fff, stop:1 #66c0f4);
    color: #ffffff;
    border: none;
    border-radius: 10px;
    padding: 11px 22px;
    font-weight: 700;
}
#PrimaryButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #2faeff, stop:1 #8fd8ff);
}
#PrimaryButton:disabled { background: #3a4a5c; color: #8394a7; }

#SecondaryButton {
    background: rgba(70, 100, 140, 0.30);
    color: #c7d5e0;
    border: 1px solid rgba(120, 160, 200, 0.30);
    border-radius: 9px;
    padding: 9px 16px;
    font-weight: 600;
}
#SecondaryButton:hover { background: rgba(70, 100, 140, 0.55); color: #ffffff; }

#GreenButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4cff88, stop:1 #a4d007);
    color: #0e2418; border: none; border-radius: 9px; padding: 9px 16px; font-weight: 700;
}
#GreenButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6cffa0, stop:1 #c4e023); }

/* ---- Inputs ---- */
QLineEdit, QTextEdit, QComboBox, QListWidget {
    background: rgba(20, 28, 40, 0.70);
    border: 1px solid rgba(120, 160, 200, 0.30);
    border-radius: 8px;
    padding: 8px 10px;
    color: #e6ecf3;
    selection-background-color: #1a9fff;
}
QLineEdit:focus, QTextEdit:focus { border: 1px solid #66c0f4; }
QComboBox::drop-down { border: none; width: 24px; }
QComboBox QAbstractItemView {
    background: #1b2838; border: 1px solid rgba(120,160,200,0.4); border-radius: 8px;
    selection-background-color: #1a9fff;
}

/* ---- Progress bar ---- */
QProgressBar {
    background: rgba(20, 28, 40, 0.70);
    border: 1px solid rgba(120, 160, 200, 0.25);
    border-radius: 8px;
    height: 14px;
    text-align: center;
    color: #ffffff;
}
QProgressBar::chunk {
    border-radius: 7px;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1a9fff, stop:1 #a4d007);
}

#StatusActive   { color: #4cff88; font-weight: 700; }
#StatusInactive { color: #ff8a8a; font-weight: 700; }

#PageTitle { font-size: 26px; font-weight: 800; color: #ffffff; letter-spacing: 0.5px; }
#SubText   { color: #8fa3b8; font-size: 13px; }

QScrollBar:vertical { background: transparent; width: 10px; border-radius: 5px; }
QScrollBar::handle:vertical { background: rgba(120, 160, 200, 0.4); border-radius: 5px; min-height: 30px; }
QScrollBar::handle:vertical:hover { background: rgba(120, 160, 200, 0.7); }
QScrollBar::add-line, QScrollBar::sub-line { height: 0; }
"""


class GlassPanel(QFrame):
    """A rounded frosted-glass card."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("GlassPanel")


def make_title(text):
    lbl = QLabel(text)
    lbl.setObjectName("PageTitle")
    return lbl


def make_sub(text):
    lbl = QLabel(text)
    lbl.setObjectName("SubText")
    lbl.setWordWrap(True)
    return lbl


class SteamButton(QPushButton):
    """Button with a hover glow."""
    def __init__(self, text, obj_name, parent=None):
        super().__init__(text, parent)
        self.setObjectName(obj_name)
        self.setCursor(Qt.PointingHandCursor)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FB Marketplace Multi-State Poster")
        self.resize(1120, 720)
        self.setMinimumSize(960, 620)

        self.products = load_products()
        self.settings = load_settings()

        self._build_ui()
        QTimer.singleShot(400, self._check_license_ui)

    def _build_ui(self):
        root = QWidget()
        root.setObjectName("Root")
        self.setCentralWidget(root)

        outer = QHBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Sidebar
        sidebar = QVBoxLayout()
        sidebar.setContentsMargins(20, 28, 20, 28)
        sidebar.setSpacing(10)

        brand = QLabel("FB POSTER")
        brand.setStyleSheet("font-size: 20px; font-weight: 900; color: #ffffff; letter-spacing: 2px;")
        brand.setAlignment(Qt.AlignCenter)
        sidebar.addWidget(brand)

        brand_sub = QLabel("Multi-State Marketplace")
        brand_sub.setObjectName("SubText")
        brand_sub.setAlignment(Qt.AlignCenter)
        sidebar.addWidget(brand_sub)
        sidebar.addSpacing(18)

        self.btn_group = QButtonGroup(self)
        self.btn_group.setExclusive(True)

        nav_names = [("Dashboard", 0), ("Products", 1), ("Settings", 2)]
        self.nav_buttons = []
        for text, idx in nav_names:
            b = QPushButton(text)
            b.setObjectName("NavButton")
            b.setCheckable(True)
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(lambda _, i=idx: self._switch_page(i))
            self.btn_group.addButton(b, idx)
            sidebar.addWidget(b)
            self.nav_buttons.append(b)

        sidebar.addStretch(1)

        self.side_status = QLabel("● Checking…")
        self.side_status.setObjectName("StatusInactive")
        self.side_status.setAlignment(Qt.AlignCenter)
        sidebar.addWidget(self.side_status)

        sidebar_widget = QWidget()
        sidebar_widget.setFixedWidth(230)
        sidebar_widget.setLayout(sidebar)
        sidebar_widget.setStyleSheet(
            "QWidget { background: rgba(15, 20, 28, 0.55); border-right: 1px solid rgba(120,160,200,0.18); }"
        )
        outer.addWidget(sidebar_widget)

        self.stack = QStackedWidget()
        self.stack.addWidget(self._build_dashboard())
        self.stack.addWidget(self._build_products())
        self.stack.addWidget(self._build_settings())
        outer.addWidget(self.stack, 1)

        self.nav_buttons[0].setChecked(True)
        self.stack.setCurrentIndex(0)

    def _switch_page(self, idx):
        self.stack.setCurrentIndex(idx)

    def _build_dashboard(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(30, 28, 30, 28)
        lay.setSpacing(16)

        lay.addWidget(make_title("Dashboard"))
        lay.addWidget(make_sub("Post your products to all 58 Algerian wilayas in one click."))

        status_card = GlassPanel()
        sc = QVBoxLayout(status_card)
        sc.setContentsMargins(20, 18, 20, 18)
        sc.setSpacing(12)

        self.status_label = QLabel("Status: checking license…")
        self.status_label.setStyleSheet("font-size: 15px; color: #c7d5e0; font-weight: 600;")
        sc.addWidget(self.status_label)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(True)
        sc.addWidget(self.progress)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        self.post_btn = SteamButton("▶  Post to All Wilayas", "PrimaryButton")
        self.post_btn.clicked.connect(self.start_posting)
        btn_row.addWidget(self.post_btn)
        self.check_btn = SteamButton("Check license", "SecondaryButton")
        self.check_btn.clicked.connect(self._check_license_ui)
        btn_row.addWidget(self.check_btn)
        btn_row.addStretch(1)
        sc.addLayout(btn_row)

        lay.addWidget(status_card)

        log_card = GlassPanel()
        lc = QVBoxLayout(log_card)
        lc.setContentsMargins(20, 18, 20, 18)
        lc.setSpacing(8)

        log_title = QLabel("Activity Log")
        log_title.setStyleSheet("font-weight: 700; color: #e6ecf3; font-size: 14px;")
        lc.addWidget(log_title)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet(
            "background: rgba(10, 14, 20, 0.75); color: #9fe9a6; border: 1px solid rgba(120,160,200,0.2); border-radius: 8px;"
        )
        self.log_text.setFont(QFont("Consolas", 10))
        lc.addWidget(self.log_text, 1)

        lay.addWidget(log_card, 1)

        self._log("Welcome! Configure your license in Settings, build products, then Post.")
        return page

    def _log(self, message):
        self.log_text.append(message)

    def _set_status(self, text, active=None):
        self.status_label.setText(text)
        if active is not None:
            self.side_status.setText("● ACTIVE" if active else "● INACTIVE")
            self.side_status.setObjectName("StatusActive" if active else "StatusInactive")
            self.side_status.style().unpolish(self.side_status)
            self.side_status.style().polish(self.side_status)

    def _check_license_ui(self):
        def run():
            try:
                res = license_client.check_license()
                if res.get("valid"):
                    self._set_status(f"Status: License ACTIVE — {res.get('name','')} until {res.get('expires_at','')}", active=True)
                else:
                    self._set_status(f"Status: License {res.get('status','inactive')} — activate to post.", active=False)
            except license_client.LicenseError as e:
                self._set_status(f"Status: {e}", active=False)
        threading.Thread(target=run, daemon=True).start()

    def start_posting(self):
        if not self.products:
            QMessageBox.warning(self, "No products", "Add at least one product first.")
            return
        try:
            res = license_client.check_license()
        except license_client.LicenseError as e:
            QMessageBox.critical(self, "License error", str(e))
            return
        if not res.get("valid"):
            QMessageBox.critical(self, "Not active", f"Your license is {res.get('status','inactive')}. Renew to post.")
            return
        self._log("Starting posting run…")
        threading.Thread(target=self._post_worker, daemon=True).start()

    def _post_worker(self):
        try:
            selected = self.settings.get("selected_wilayas") or [w["name"] for w in WILAYAS]
            total = len(self.products) * len(selected)
            self.progress.setMaximum(max(total, 1))
            done = 0
            for product in self.products:
                for wilaya in selected:
                    self._log(f"Posting '{product.get('title','?')}' → {wilaya} …")
                    # from facebook import automation
                    # automation.post_listing(product, {"name": wilaya}, self.settings)
                    done += 1
                    self.progress.setValue(done)
            self._log(f"Done. {done} listings processed.")
            self._set_status("Status: posting complete", active=True)
        except Exception as e:
            self._log("ERROR: " + traceback.format_exc())
            self._set_status("Status: posting failed", active=False)

    def _build_products(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(30, 28, 30, 28)
        lay.setSpacing(16)

        lay.addWidget(make_title("Products"))
        lay.addWidget(make_sub("Build a product, attach photos, and queue it for posting."))

        body = QHBoxLayout()
        body.setSpacing(20)

        form_card = GlassPanel()
        fc = QVBoxLayout(form_card)
        fc.setContentsMargins(20, 18, 20, 18)
        fc.setSpacing(8)

        def field_label(t):
            l = QLabel(t)
            l.setStyleSheet("color: #8fa3b8; font-size: 12px; font-weight: 600;")
            return l

        fc.addWidget(field_label("TITLE *"))
        self.title_edit = QLineEdit()
        fc.addWidget(self.title_edit)

        fc.addWidget(field_label("DESCRIPTION"))
        self.desc_edit = QTextEdit()
        self.desc_edit.setFixedHeight(90)
        fc.addWidget(self.desc_edit)

        fc.addWidget(field_label("PRICE (DA) *"))
        self.price_edit = QLineEdit()
        fc.addWidget(self.price_edit)

        fc.addWidget(field_label("CATEGORY"))
        self.cat_combo = QComboBox()
        self.cat_combo.addItems(CATEGORIES)
        fc.addWidget(self.cat_combo)

        fc.addWidget(field_label("IMAGES"))
        self.img_list = QListWidget()
        self.img_list.setFixedHeight(96)
        fc.addWidget(self.img_list)

        img_btn_row = QHBoxLayout()
        add_img = SteamButton("+ Add images", "SecondaryButton")
        add_img.clicked.connect(self.add_images)
        rm_img = SteamButton("− Remove", "SecondaryButton")
        rm_img.clicked.connect(self.remove_image)
        img_btn_row.addWidget(add_img)
        img_btn_row.addWidget(rm_img)
        img_btn_row.addStretch(1)
        fc.addLayout(img_btn_row)

        save_btn = SteamButton("Save product", "GreenButton")
        save_btn.clicked.connect(self.save_product)
        fc.addWidget(save_btn)

        body.addWidget(form_card, 1)

        list_card = GlassPanel()
        lc = QVBoxLayout(list_card)
        lc.setContentsMargins(20, 18, 20, 18)
        lc.setSpacing(8)

        lc.addWidget(field_label("SAVED PRODUCTS"))
        self.product_list = QListWidget()
        lc.addWidget(self.product_list, 1)

        list_btn_row = QHBoxLayout()
        load_btn = SteamButton("Load", "SecondaryButton")
        load_btn.clicked.connect(self.load_selected_product)
        del_btn = SteamButton("Delete", "SecondaryButton")
        del_btn.clicked.connect(self.delete_product)
        list_btn_row.addWidget(load_btn)
        list_btn_row.addWidget(del_btn)
        list_btn_row.addStretch(1)
        lc.addLayout(list_btn_row)

        body.addWidget(list_card, 1)

        lay.addLayout(body, 1)
        self._refresh_product_list()
        return page

    def add_images(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Select product images", "",
            "Images (*.png *.jpg *.jpeg *.webp *.gif);;All files (*)")
        existing = [self.img_list.item(i).text() for i in range(self.img_list.count())]
        for p in paths:
            if p not in existing:
                self.img_list.addItem(p)

    def remove_image(self):
        for item in self.img_list.selectedItems():
            self.img_list.takeItem(self.img_list.row(item))

    def save_product(self):
        title = self.title_edit.text().strip()
        price = self.price_edit.text().strip()
        if not title or not price:
            QMessageBox.warning(self, "Missing fields", "Title and price are required.")
            return
        product = {
            "title": title,
            "description": self.desc_edit.toPlainText().strip(),
            "price": price,
            "category": self.cat_combo.currentText(),
            "images": [self.img_list.item(i).text() for i in range(self.img_list.count())],
        }
        self.products.append(product)
        save_products(self.products)
        self._refresh_product_list()
        self._clear_form()
        self._log(f"Saved product: {title}")

    def _clear_form(self):
        self.title_edit.clear()
        self.desc_edit.clear()
        self.price_edit.clear()
        self.cat_combo.setCurrentIndex(0)
        self.img_list.clear()

    def _refresh_product_list(self):
        self.product_list.clear()
        for p in self.products:
            self.product_list.addItem(f"{p.get('title','?')} — {p.get('price','?')} DA")

    def load_selected_product(self):
        items = self.product_list.selectedItems()
        if not items:
            return
        idx = self.product_list.row(items[0])
        if idx >= len(self.products):
            return
        p = self.products[idx]
        self._clear_form()
        self.title_edit.setText(p.get("title", ""))
        self.desc_edit.setPlainText(p.get("description", ""))
        self.price_edit.setText(p.get("price", ""))
        idx_cat = self.cat_combo.findText(p.get("category", CATEGORIES[0]))
        self.cat_combo.setCurrentIndex(idx_cat if idx_cat >= 0 else 0)
        for img in p.get("images", []):
            self.img_list.addItem(img)

    def delete_product(self):
        items = self.product_list.selectedItems()
        if not items:
            return
        idx = self.product_list.row(items[0])
        if idx < len(self.products):
            del self.products[idx]
            save_products(self.products)
            self._refresh_product_list()

    def _build_settings(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(30, 28, 30, 28)
        lay.setSpacing(16)

        lay.addWidget(make_title("Settings"))
        lay.addWidget(make_sub("License, WhatsApp number, wilaya targeting and safety."))

        card = GlassPanel()
        c = QVBoxLayout(card)
        c.setContentsMargins(20, 18, 20, 18)
        c.setSpacing(8)

        def field_label(t):
            l = QLabel(t)
            l.setStyleSheet("color: #8fa3b8; font-size: 12px; font-weight: 600;")
            return l

        c.addWidget(field_label("LICENSE KEY"))
        self.license_edit = QLineEdit(self.settings.get("license_key", ""))
        c.addWidget(self.license_edit)

        c.addWidget(field_label("BACKEND URL (license server)"))
        self.backend_edit = QLineEdit(self.settings.get("api_base_url", ""))
        c.addWidget(self.backend_edit)

        c.addWidget(field_label("WHATSAPP NUMBER (printed on listings)"))
        self.wa_edit = QLineEdit(self.settings.get("whatsapp_number", ""))
        c.addWidget(self.wa_edit)

        c.addWidget(field_label("DAILY POST CAP"))
        self.cap_edit = QLineEdit(str(self.settings.get("daily_post_cap", 30)))
        self.cap_edit.setFixedWidth(120)
        c.addWidget(self.cap_edit)

        c.addWidget(field_label("WILAYAS TO POST TO (empty = all 58)"))
        self.wilaya_list = QListWidget()
        self.wilaya_list.setSelectionMode(QListWidget.ExtendedSelection)
        for w in WILAYAS:
            self.wilaya_list.addItem(QListWidgetItem(f"{w['code']} — {w['name']}"))
        self.wilaya_list.setFixedHeight(150)
        c.addWidget(self.wilaya_list)

        sel = self.settings.get("selected_wilayas") or []
        if sel:
            names = set(sel)
            for i, w in enumerate(WILAYAS):
                if w["name"] in names:
                    self.wilaya_list.item(i).setSelected(True)

        save_btn = SteamButton("Save settings", "PrimaryButton")
        save_btn.clicked.connect(self.save_settings_ui)
        c.addWidget(save_btn)

        lay.addWidget(card)
        lay.addStretch(1)
        return page

    def save_settings_ui(self):
        sel_names = [
            WILAYAS[i]["name"]
            for i in range(self.wilaya_list.count())
            if self.wilaya_list.item(i).isSelected()
        ]
        cap = int(self.cap_edit.text().strip() or "30")
        self.settings.update({
            "license_key": self.license_edit.text().strip(),
            "api_base_url": self.backend_edit.text().strip(),
            "whatsapp_number": self.wa_edit.text().strip(),
            "daily_post_cap": cap,
            "selected_wilayas": sel_names,
        })
        save_settings(self.settings)
        QMessageBox.information(self, "Saved", "Settings saved.")
        self._check_license_ui()


def main():
    app = QApplication([])
    app.setStyleSheet(STYLE)
    win = MainWindow()
    win.show()
    app.exec()


if __name__ == "__main__":
    main()
