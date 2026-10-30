
import argparse
import hashlib
import hmac
import json
import os
import secrets
import sys
from datetime import datetime, date

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QFontDatabase, QPainter, QPainterPath
from PyQt6.QtWidgets import (
    QApplication, QComboBox, QDialog, QFileDialog, QFrame, QGraphicsDropShadowEffect,
    QGridLayout, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QMainWindow,
    QMessageBox, QPushButton, QScrollArea, QSizePolicy, QSpacerItem,
    QStackedWidget, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

import logic
import menu as menu_module
from menu import RESTAURANT_NAME

# ---------- palette ----------
GREEN      = "#0DAA5F"
GREEN_DARK = "#098B4C"
DARK       = "#2B2B2B"
TEXT       = "#333333"
MUTED      = "#8A8A8A"
LINE       = "#EAEAEA"
BG         = "#F3F3F3"
RED        = "#D32F2F"
AMBER      = "#F59E0B"
BLUE       = "#2563EB"

# ---------- files ----------
_DIR = os.path.dirname(os.path.abspath(__file__))
ADMIN_CREDS_FILE = os.path.join(_DIR, "admin_credentials.json")

# ---------- style ----------
ADMIN_EXTRA_STYLE = f"""
* {{ font-family: 'Roboto', sans-serif; }}
/* nav sidebar */
QPushButton#nav {{
    background: {DARK}; color: #CCCCCC; border: none; border-radius: 0;
    text-align: left; padding: 14px 20px; font-size: 11px; font-weight: bold;
}}
QPushButton#nav:hover {{ background: #3A3A3A; color: white; }}
QPushButton#nav:checked {{ background: {GREEN}; color: white; }}

/* summary cards */
QFrame#statCard {{ background: white; border: 1px solid {LINE}; border-radius: 4px; }}
QLabel#statValue {{ font-size: 22px; font-weight: bold; color: {TEXT}; }}
QLabel#statLabel {{ font-size: 10px; color: {MUTED}; font-weight: bold; }}

/* page headings */
QLabel#pageTitle {{ font-size: 16px; font-weight: bold; color: {TEXT}; }}

/* admin topbar */
QFrame#adminTopbar {{ background: {DARK}; }}
QLabel#adminTitle {{ font-size: 15px; font-weight: bold; color: white; }}
QLabel#adminSub   {{ font-size: 10px; color: #AAAAAA; }}

/* table */
QTableWidget {{
    background: white; border: 1px solid {LINE}; border-radius: 3px;
    gridline-color: {LINE}; font-size: 11px;
}}
QHeaderView::section {{
    background: {BG}; color: {TEXT}; border: none;
    border-bottom: 1px solid {LINE}; padding: 6px 8px;
    font-size: 10px; font-weight: bold;
}}
QTableWidget::item {{ padding: 4px 8px; }}
QTableWidget::item:selected {{ background: #E8F5EE; color: {TEXT}; }}

/* inline status badges */
QLabel#badge_pending   {{ background: {AMBER}; color: white; border-radius: 3px; padding: 2px 6px; font-size: 10px; }}
QLabel#badge_completed {{ background: {GREEN}; color: white; border-radius: 3px; padding: 2px 6px; font-size: 10px; }}
QLabel#badge_cancelled {{ background: {RED};   color: white; border-radius: 3px; padding: 2px 6px; font-size: 10px; }}

/* table action buttons */
QPushButton#actionEdit {{
    background: white; color: {GREEN}; border: 1px solid {GREEN};
    border-radius: 3px; font-size: 11px; font-weight: bold; padding: 0px 8px;
}}
QPushButton#actionEdit:hover {{ background: #F1FBF6; }}

QPushButton#actionDelete {{
    background: {RED}; color: white; border: none;
    border-radius: 3px; font-size: 11px; font-weight: bold; padding: 0px 8px;
}}
QPushButton#actionDelete:hover {{ background: #B71C1C; }}

QPushButton#actionComplete {{
    background: {GREEN}; color: white; border: none;
    border-radius: 3px; font-size: 11px; font-weight: bold; padding: 0px 8px;
}}
QPushButton#actionComplete:hover {{ background: {GREEN_DARK}; }}

QPushButton#actionCancel {{
    background: white; color: {RED}; border: 1px solid {RED};
    border-radius: 3px; font-size: 11px; font-weight: bold; padding: 0px 8px;
}}
QPushButton#actionCancel:hover {{ background: #FEEEEE; }}

/* admin auth */
QWidget#adminAuthBg {{ background-color: #E8ECF4; }}
"""


# ---------- credential helpers ----------

def _hash(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt), 200_000
    ).hex()


def _load_admin_creds():
    if not os.path.exists(ADMIN_CREDS_FILE):
        return None
    with open(ADMIN_CREDS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_admin_creds(username: str, password: str):
    salt = secrets.token_hex(16)
    data = {"username": username, "salt": salt, "hash": _hash(password, salt)}
    with open(ADMIN_CREDS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def verify_admin(username: str, password: str) -> bool:
    creds = _load_admin_creds()
    if creds is None:
        return False
    if username.strip().lower() != creds["username"].lower():
        return False
    return hmac.compare_digest(_hash(password, creds["salt"]), creds["hash"])


def admin_exists() -> bool:
    return os.path.exists(ADMIN_CREDS_FILE)


# ---------- order store ----------

def get_all_orders() -> list[dict]:
    try:
        return logic.load_orders()
    except OSError:
        return []


def update_order_status(order_number: str, status: str) -> bool:
    try:
        orders = logic.load_orders()
        for o in orders:
            if o["order_number"] == order_number:
                o["status"] = status
                break
        logic.save_orders(orders)
        return True
    except OSError:
        return False


# ---------- shared ui helpers ----------

class _AuthCard(QWidget):
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(), QColor("white"))
        w, h = self.width(), self.height()
        tri = QPainterPath()
        tri.moveTo(0, 0)
        tri.lineTo(w * 0.6, 0)
        tri.lineTo(0, h)
        tri.closeSubpath()
        p.fillPath(tri, QColor(GREEN))
        p.end()


def _make_field(label_text: str, placeholder: str, password=False):
    lbl = QLabel(f"{label_text}<span style='color:#E53935;'>*</span>")
    lbl.setTextFormat(Qt.TextFormat.RichText)
    lbl.setObjectName("fieldLabel")
    box = QLineEdit()
    box.setObjectName("authInput")
    box.setPlaceholderText(placeholder)
    if password:
        box.setEchoMode(QLineEdit.EchoMode.Password)
    return lbl, box


def _stat_card(value_text: str, label_text: str, color: str = TEXT) -> QFrame:
    card = QFrame()
    card.setObjectName("statCard")
    lay = QVBoxLayout(card)
    lay.setContentsMargins(16, 14, 16, 14)
    lay.setSpacing(2)
    val = QLabel(value_text)
    val.setObjectName("statValue")
    val.setStyleSheet(f"font-size:22px; font-weight:bold; color:{color};")
    lbl = QLabel(label_text.upper())
    lbl.setObjectName("statLabel")
    lay.addWidget(val)
    lay.addWidget(lbl)
    return card, val


def _section_title(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setObjectName("pageTitle")
    return lbl


def _page_scroll(inner: QWidget) -> QScrollArea:
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setWidget(inner)
    return scroll


# ---------- admin login window ----------

class AdminLoginWindow(QWidget):

    authenticated = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("adminAuthBg")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setWindowTitle(f"{RESTAURANT_NAME} – Admin")
        self.resize(760, 520)
        self.setMinimumSize(640, 440)
        self.setWindowFlags(Qt.WindowType.Window)

        outer = QVBoxLayout(self)
        card = _AuthCard()
        card.setFixedSize(620, 400)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(25)
        shadow.setOffset(0, 3)
        shadow.setColor(QColor(0, 0, 0, 60))
        card.setGraphicsEffect(shadow)
        outer.addWidget(card, alignment=Qt.AlignmentFlag.AlignCenter)

        row = QHBoxLayout(card)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(0)
        row.addWidget(self._build_left())
        row.addWidget(self._build_right(), 1)

        self._center()

    # ---------- build ----------
    def _build_left(self):
        left = QWidget()
        left.setFixedWidth(280)
        lay = QVBoxLayout(left)
        lay.setContentsMargins(32, 44, 0, 0)
        lay.setSpacing(10)

        title = QLabel("Admin\nAccess")
        title.setObjectName("welcome")
        sub = QLabel("Restricted area.\nAuthorised personnel only.")
        sub.setObjectName("welcomeText")
        sub.setWordWrap(True)
        sub.setFixedWidth(180)

        back_btn = QPushButton("← Back to Login")
        back_btn.setObjectName("outlineWhite")
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.clicked.connect(self.close)

        lay.addWidget(title)
        lay.addWidget(sub)
        lay.addSpacing(8)
        lay.addWidget(back_btn, alignment=Qt.AlignmentFlag.AlignLeft)
        lay.addStretch()
        return left

    def _build_right(self):
        right = QWidget()
        lay = QVBoxLayout(right)
        lay.setContentsMargins(34, 36, 36, 0)

        heading = QLabel("Administrator Login")
        heading.setObjectName("authTitle")
        lay.addWidget(heading)
        lay.addSpacing(10)

        lbl_u, self.user_box = _make_field("Username", "Admin username")
        lbl_p, self.pass_box = _make_field("Password", "Password", password=True)
        lay.addWidget(lbl_u)
        lay.addWidget(self.user_box)
        lay.addSpacing(6)
        lay.addWidget(lbl_p)

        pass_row = QHBoxLayout()
        pass_row.setSpacing(6)
        pass_row.addWidget(self.pass_box, 1)
        self.eye_btn = QPushButton("Show")
        self.eye_btn.setObjectName("ghost")
        self.eye_btn.setFixedHeight(28)
        self.eye_btn.setToolTip("Show / hide password")
        self.eye_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.eye_btn.setCheckable(True)
        self.eye_btn.toggled.connect(self._toggle_eye)
        pass_row.addWidget(self.eye_btn)
        lay.addLayout(pass_row)
        lay.addSpacing(10)

        login_btn = QPushButton("Sign In")
        login_btn.setObjectName("authSubmit")
        login_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        login_btn.clicked.connect(self._on_login)
        lay.addWidget(login_btn)

        self.status_lbl = QLabel("")
        self.status_lbl.setWordWrap(True)
        lay.addWidget(self.status_lbl)
        lay.addStretch()

        self.pass_box.returnPressed.connect(login_btn.click)
        return right

    # ---------- logic ----------
    def _toggle_eye(self, checked):
        mode = QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
        self.pass_box.setEchoMode(mode)
        self.eye_btn.setText("Hide" if checked else "Show")

    def _on_login(self):
        if not admin_exists():
            self._show_status("No admin account configured. Run:  python admingui.py --setup")
            return
        if verify_admin(self.user_box.text(), self.pass_box.text()):
            self.pass_box.clear()
            self.authenticated.emit()
            self.close()
        else:
            self._show_status("Incorrect username or password.")

    def _show_status(self, msg, ok=False):
        color = GREEN if ok else RED
        self.status_lbl.setStyleSheet(f"color:{color}; font-size:11px;")
        self.status_lbl.setText(msg)

    def _center(self):
        screen = self.screen() or QApplication.primaryScreen()
        if screen:
            r = screen.availableGeometry()
            self.move(r.x() + (r.width() - self.width()) // 2,
                      r.y() + (r.height() - self.height()) // 2)

    def showEvent(self, event):
        super().showEvent(event)
        self._center()


# ---------- dashboard page ----------

class DashboardPage(QWidget):
    def __init__(self):
        super().__init__()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(16)
        lay.addWidget(_section_title("Dashboard"))

        grid = QGridLayout()
        grid.setSpacing(12)

        self._cards = {}
        specs = [
            ("today_rev",   "₱0.00",  "Today's Revenue",   GREEN),
            ("total_orders","0",       "Total Orders",      TEXT),
            ("pending",     "0",       "Pending Orders",    AMBER),
            ("completed",   "0",       "Completed Orders",  GREEN),
            ("cancelled",   "0",       "Cancelled Orders",  RED),
            ("menu_items",  "0",       "Menu Items",        BLUE),
            ("customers",   "0",       "Registered Customers", TEXT),
        ]
        for i, (key, val, lbl, clr) in enumerate(specs):
            card, val_lbl = _stat_card(val, lbl, clr)
            self._cards[key] = val_lbl
            grid.addWidget(card, i // 4, i % 4)

        lay.addLayout(grid)

        lay.addWidget(_section_title("Recent Orders"))
        self.table = self._make_table(
            ["Order #", "Customer", "Type", "Total", "Payment", "Status", "Time"])
        lay.addWidget(self.table, 1)

        self.refresh()

    def _make_table(self, headers):
        t = QTableWidget(0, len(headers))
        t.setHorizontalHeaderLabels(headers)
        t.verticalHeader().setVisible(False)
        t.verticalHeader().setDefaultSectionSize(36)
        t.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        t.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        t.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        t.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        t.horizontalHeader().setStretchLastSection(False)
        return t

    def refresh(self):
        orders = get_all_orders()
        today  = date.today().isoformat()

        today_rev  = sum(o["total"] for o in orders
                         if o.get("time", "").startswith(today))
        pending    = sum(1 for o in orders if o.get("status") == "Pending")
        completed  = sum(1 for o in orders if o.get("status") == "Completed")
        cancelled  = sum(1 for o in orders if o.get("status") == "Cancelled")
        customers  = len(logic.load_accounts())
        menu_items = len(menu_module.get_all_items())

        self._cards["today_rev"].setText(logic.format_price(today_rev))
        self._cards["total_orders"].setText(str(len(orders)))
        self._cards["pending"].setText(str(pending))
        self._cards["completed"].setText(str(completed))
        self._cards["cancelled"].setText(str(cancelled))
        self._cards["menu_items"].setText(str(menu_items))
        self._cards["customers"].setText(str(customers))

        recent = orders[-20:][::-1]
        self.table.setRowCount(len(recent))
        for r, o in enumerate(recent):
            cells = [
                o.get("order_number", ""),
                o.get("customer", ""),
                o.get("order_type", ""),
                logic.format_price(o.get("total", 0)),
                o.get("payment", ""),
                o.get("status", "Pending"),
                o.get("time", ""),
            ]
            for c, val in enumerate(cells):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                self.table.setItem(r, c, item)


# ---------- orders page ----------

class OrdersPage(QWidget):
    def __init__(self):
        super().__init__()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(12)

        top = QHBoxLayout()
        top.addWidget(_section_title("Orders"))
        top.addStretch()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search by customer or order #")
        self.search.setFixedWidth(260)
        self.search.textChanged.connect(self._filter)
        self.status_filter = QComboBox()
        self.status_filter.addItems(["All Statuses", "Pending", "Completed", "Cancelled"])
        self.status_filter.currentTextChanged.connect(self._filter)
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setObjectName("ghost")
        refresh_btn.clicked.connect(self.refresh)
        top.addWidget(self.search)
        top.addWidget(self.status_filter)
        top.addWidget(refresh_btn)
        lay.addLayout(top)

        cols = ["Order #", "Customer", "Phone", "Type", "Payment",
                "Subtotal", "Delivery", "Total", "Status", "Time", "Actions"]
        self.table = QTableWidget(0, len(cols))
        self.table.setHorizontalHeaderLabels(cols)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(42)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.setColumnWidth(10, 180)
        lay.addWidget(self.table, 1)

        self._all_orders = []
        self.refresh()

    def refresh(self):
        self._all_orders = get_all_orders()[::-1]
        self._filter()

    def _filter(self):
        query  = self.search.text().strip().lower()
        status = self.status_filter.currentText()
        rows   = [
            o for o in self._all_orders
            if (not query or query in o.get("order_number","").lower()
                          or query in o.get("customer","").lower())
            and (status == "All Statuses" or o.get("status") == status)
        ]
        self._populate(rows)

    def _populate(self, orders):
        self.table.setRowCount(len(orders))
        for r, o in enumerate(orders):
            vals = [
                o.get("order_number",""),
                o.get("customer",""),
                o.get("phone",""),
                o.get("order_type",""),
                o.get("payment",""),
                logic.format_price(o.get("subtotal",0)),
                logic.format_price(o.get("delivery_fee",0)),
                logic.format_price(o.get("total",0)),
                o.get("status","Pending"),
                o.get("time",""),
            ]
            for c, val in enumerate(vals):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                self.table.setItem(r, c, item)

            cell = QWidget()
            cell_lay = QHBoxLayout(cell)
            cell_lay.setContentsMargins(6, 4, 6, 4)
            cell_lay.setSpacing(6)
            cell_lay.setAlignment(Qt.AlignmentFlag.AlignLeft)
            cur_status = o.get("status", "Pending")
            order_num  = o.get("order_number", "")
            if cur_status == "Pending":
                done_btn = QPushButton("Complete")
                done_btn.setObjectName("actionComplete")
                done_btn.setFixedSize(76, 28)
                done_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                done_btn.clicked.connect(lambda _, n=order_num: self._set_status(n, "Completed"))

                cancel_btn = QPushButton("Cancel")
                cancel_btn.setObjectName("actionCancel")
                cancel_btn.setFixedSize(68, 28)
                cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                cancel_btn.clicked.connect(lambda _, n=order_num: self._set_status(n, "Cancelled"))

                cell_lay.addWidget(done_btn)
                cell_lay.addWidget(cancel_btn)
                cell_lay.addStretch()
            else:
                badge = QLabel(cur_status)
                badge_key = cur_status.lower()
                badge.setObjectName(f"badge_{badge_key}")
                cell_lay.addWidget(badge)
                cell_lay.addStretch()
            self.table.setCellWidget(r, 10, cell)

    def _set_status(self, order_num, status):
        if not update_order_status(order_num, status):
            QMessageBox.warning(self, "Could not save",
                                "The order status could not be saved. Please try again.")
            return
        self.refresh()


# ---------- menu management page ----------

class MenuPage(QWidget):

    def __init__(self):
        super().__init__()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(12)

        top = QHBoxLayout()
        top.addWidget(_section_title("Menu Management"))
        top.addStretch()
        add_btn = QPushButton("+ Add Item")
        add_btn.clicked.connect(self._add_item)
        top.addWidget(add_btn)
        lay.addLayout(top)

        cols = ["ID", "Name", "Category", "Price", "Actions"]
        self.table = QTableWidget(0, len(cols))
        self.table.setHorizontalHeaderLabels(cols)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(42)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.setColumnWidth(4, 170)
        lay.addWidget(self.table, 1)

        self.refresh()

    def refresh(self):
        items = menu_module.get_all_items()
        self.table.setRowCount(len(items))
        for r, item in enumerate(items):
            for c, val in enumerate([
                str(item["id"]), item["name"], item["category"],
                logic.format_price(item["price"]),
            ]):
                ti = QTableWidgetItem(val)
                ti.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                self.table.setItem(r, c, ti)

            cell = QWidget()
            cell_lay = QHBoxLayout(cell)
            cell_lay.setContentsMargins(6, 4, 6, 4)
            cell_lay.setSpacing(8)
            cell_lay.setAlignment(Qt.AlignmentFlag.AlignLeft)

            edit_btn = QPushButton("Edit")
            edit_btn.setObjectName("actionEdit")
            edit_btn.setFixedSize(68, 28)
            edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            edit_btn.clicked.connect(lambda _, i=item: self._edit_item(i))

            del_btn = QPushButton("Delete")
            del_btn.setObjectName("actionDelete")
            del_btn.setFixedSize(68, 28)
            del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            del_btn.clicked.connect(lambda _, i=item: self._delete_item(i))

            cell_lay.addWidget(edit_btn)
            cell_lay.addWidget(del_btn)
            cell_lay.addStretch()
            self.table.setCellWidget(r, 4, cell)

    def _save(self):
        try:
            menu_module.save_menu()
        except OSError:
            QMessageBox.warning(self, "Could not save",
                                "The menu change could not be saved to disk.")

    def _add_item(self):
        dlg = MenuItemDialog(self)
        if dlg.exec():
            data = dlg.get_data()
            new_id = max((i["id"] for i in menu_module.MENU_ITEMS), default=0) + 1
            data["id"] = new_id
            menu_module.MENU_ITEMS.append(data)
            self._save()
            self.refresh()

    def _edit_item(self, item):
        dlg = MenuItemDialog(self, item)
        if dlg.exec():
            data = dlg.get_data()
            data["id"] = item["id"]
            idx = next((i for i, x in enumerate(menu_module.MENU_ITEMS)
                        if x["id"] == item["id"]), None)
            if idx is not None:
                menu_module.MENU_ITEMS[idx] = data
            self._save()
            self.refresh()

    def _delete_item(self, item):
        ans = QMessageBox.question(
            self, "Confirm Delete",
            f"Delete '{item['name']}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if ans == QMessageBox.StandardButton.Yes:
            menu_module.MENU_ITEMS[:] = [
                x for x in menu_module.MENU_ITEMS if x["id"] != item["id"]]
            self._save()
            self.refresh()


class MenuItemDialog(QDialog):
    def __init__(self, parent=None, item=None):
        super().__init__(parent)
        self.setWindowTitle("Add Item" if item is None else "Edit Item")
        self.setMinimumWidth(380)
        lay = QVBoxLayout(self)
        lay.setSpacing(8)

        cats = [c for c in menu_module.CATEGORIES if c != "All"]

        def row(label, widget):
            l = QLabel(label)
            l.setObjectName("fieldLabel")
            lay.addWidget(l)
            lay.addWidget(widget)

        self.name_box = QLineEdit(item["name"] if item else "")
        self.name_box.setObjectName("authInput")
        row("Name *", self.name_box)

        self.cat_combo = QComboBox()
        self.cat_combo.addItems(cats)
        if item:
            idx = self.cat_combo.findText(item["category"])
            if idx >= 0:
                self.cat_combo.setCurrentIndex(idx)
        row("Category *", self.cat_combo)

        self.price_box = QLineEdit(str(item["price"]) if item else "")
        self.price_box.setObjectName("authInput")
        self.price_box.setPlaceholderText("e.g. 149.00")
        row("Price (₱) *", self.price_box)

        self.desc_box = QLineEdit(item.get("description","") if item else "")
        self.desc_box.setObjectName("authInput")
        row("Description", self.desc_box)

        self._image = item.get("image") if item else None
        self._picked_file = None
        pic_row = QHBoxLayout()
        self.pic_lbl = QLabel(os.path.basename(self._image) if self._image else "No picture")
        self.pic_lbl.setObjectName("desc")
        browse = QPushButton("Choose picture...")
        browse.setObjectName("ghost")
        browse.clicked.connect(self._browse_picture)
        pic_row.addWidget(self.pic_lbl, 1)
        pic_row.addWidget(browse)
        pic_label = QLabel("Picture")
        pic_label.setObjectName("fieldLabel")
        lay.addWidget(pic_label)
        lay.addLayout(pic_row)

        self.status_lbl = QLabel("")
        lay.addWidget(self.status_lbl)

        btns = QHBoxLayout()
        save = QPushButton("Save")
        save.clicked.connect(self._validate)
        cancel = QPushButton("Cancel")
        cancel.setObjectName("ghost")
        cancel.clicked.connect(self.reject)
        btns.addStretch()
        btns.addWidget(cancel)
        btns.addWidget(save)
        lay.addLayout(btns)

    def _browse_picture(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Choose a picture", "",
            "Images (*.jpg *.jpeg *.png *.webp *.bmp)")
        if path:
            self._picked_file = path
            self.pic_lbl.setText(os.path.basename(path))

    def _validate(self):
        name  = self.name_box.text().strip()
        price = self.price_box.text().strip()
        if not name:
            self._err("Name is required.")
            return
        try:
            value = float(price)
        except ValueError:
            self._err("Price must be a number.")
            return
        if not (0 < value < 100000):
            self._err("Price must be greater than 0.")
            return
        if self._picked_file:
            try:
                self._image = menu_module.import_image(self._picked_file)
            except OSError:
                self._err("Could not copy that picture. Try another file.")
                return
        self.accept()

    def _err(self, msg):
        self.status_lbl.setStyleSheet(f"color:{RED}; font-size:11px;")
        self.status_lbl.setText(msg)

    def get_data(self) -> dict:
        return {
            "name":        self.name_box.text().strip(),
            "category":    self.cat_combo.currentText(),
            "price":       float(self.price_box.text().strip()),
            "description": self.desc_box.text().strip(),
            "image":       self._image,
        }


# ---------- customers page ----------

class CustomersPage(QWidget):
    def __init__(self):
        super().__init__()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(12)

        top = QHBoxLayout()
        top.addWidget(_section_title("Customers"))
        top.addStretch()
        ref = QPushButton("Refresh")
        ref.setObjectName("ghost")
        ref.clicked.connect(self.refresh)
        top.addWidget(ref)
        lay.addLayout(top)

        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Username", "Email"])
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(36)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        lay.addWidget(self.table, 1)

        self.refresh()

    def refresh(self):
        accounts = logic.load_accounts()
        self.table.setRowCount(len(accounts))
        for r, acc in enumerate(accounts):
            self.table.setItem(r, 0, QTableWidgetItem(acc["username"]))
            self.table.setItem(r, 1, QTableWidgetItem(acc["email"]))


# ---------- reports page ----------

class ReportsPage(QWidget):
    def __init__(self):
        super().__init__()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(16)
        lay.addWidget(_section_title("Reports"))

        self.summary_lbl = QLabel()
        self.summary_lbl.setWordWrap(True)
        lay.addWidget(self.summary_lbl)

        lay.addWidget(_section_title("Popular Items"))
        self.pop_table = QTableWidget(0, 3)
        self.pop_table.setHorizontalHeaderLabels(["Item", "Qty Sold", "Revenue"])
        self.pop_table.verticalHeader().setVisible(False)
        self.pop_table.verticalHeader().setDefaultSectionSize(36)
        self.pop_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.pop_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        lay.addWidget(self.pop_table, 1)

        self.refresh()

    def refresh(self):
        orders = get_all_orders()
        total_rev   = sum(o.get("total", 0) for o in orders)
        by_payment  = {}
        by_type     = {}
        item_counts = {}

        for o in orders:
            pm = o.get("payment", "Unknown")
            ot = o.get("order_type", "Unknown")
            by_payment[pm] = by_payment.get(pm, 0) + o.get("total", 0)
            by_type[ot]    = by_type.get(ot, 0) + 1
            for line in o.get("lines", []):
                name = line.get("name", "?")
                qty  = line.get("quantity", 0)
                sub  = line.get("subtotal", 0)
                prev = item_counts.get(name, (0, 0))
                item_counts[name] = (prev[0] + qty, prev[1] + sub)

        lines = [f"<b>Total Revenue:</b> {logic.format_price(total_rev)}<br>"]
        lines.append("<b>By Payment Method:</b> " +
                     ", ".join(f"{k}: {logic.format_price(v)}" for k, v in by_payment.items()))
        lines.append("<br><b>By Order Type:</b> " +
                     ", ".join(f"{k}: {v}" for k, v in by_type.items()))
        self.summary_lbl.setText("".join(lines))

        sorted_items = sorted(item_counts.items(), key=lambda x: -x[1][0])
        self.pop_table.setRowCount(len(sorted_items))
        for r, (name, (qty, rev)) in enumerate(sorted_items):
            self.pop_table.setItem(r, 0, QTableWidgetItem(name))
            self.pop_table.setItem(r, 1, QTableWidgetItem(str(qty)))
            self.pop_table.setItem(r, 2, QTableWidgetItem(logic.format_price(rev)))


# ---------- settings page ----------

class SettingsPage(QWidget):
    def __init__(self):
        super().__init__()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(14)
        lay.addWidget(_section_title("Settings"))

        frame = QFrame()
        frame.setObjectName("surface")
        frame.setStyleSheet("background:white; border:1px solid #EAEAEA; border-radius:4px;")
        f_lay = QVBoxLayout(frame)
        f_lay.setContentsMargins(20, 18, 20, 20)
        f_lay.setSpacing(8)

        f_lay.addWidget(QLabel("<b>Change Admin Password</b>"))

        lbl_old, self.old_pass  = _make_field("Current Password", "Current password", password=True)
        lbl_new, self.new_pass  = _make_field("New Password", "New password (min 8 chars)", password=True)
        lbl_cnf, self.conf_pass = _make_field("Confirm New Password", "Re-enter new password", password=True)
        for w in (lbl_old, self.old_pass, lbl_new, self.new_pass, lbl_cnf, self.conf_pass):
            f_lay.addWidget(w)

        self.chg_status = QLabel("")
        f_lay.addWidget(self.chg_status)

        save_btn = QPushButton("Update Password")
        save_btn.setFixedWidth(160)
        save_btn.clicked.connect(self._change_password)
        f_lay.addWidget(save_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        lay.addWidget(frame)
        lay.addStretch()

    def _change_password(self):
        creds = _load_admin_creds()
        if creds is None:
            self._err("No admin account found.")
            return
        old = self.old_pass.text()
        new = self.new_pass.text()
        cnf = self.conf_pass.text()

        if not verify_admin(creds["username"], old):
            self._err("Current password is incorrect.")
            return
        if len(new) < 8:
            self._err("New password must be at least 8 characters.")
            return
        if new != cnf:
            self._err("Passwords do not match.")
            return
        _save_admin_creds(creds["username"], new)
        for b in (self.old_pass, self.new_pass, self.conf_pass):
            b.clear()
        self.chg_status.setStyleSheet(f"color:{GREEN}; font-size:11px;")
        self.chg_status.setText("Password updated successfully.")

    def _err(self, msg):
        self.chg_status.setStyleSheet(f"color:{RED}; font-size:11px;")
        self.chg_status.setText(msg)


# ---------- admin dashboard ----------

class AdminDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{RESTAURANT_NAME} – Admin Dashboard")
        self.resize(1100, 700)
        self.setMinimumSize(900, 560)

        root = QWidget()
        root.setObjectName("root")
        self.setCentralWidget(root)
        outer = QHBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        outer.addWidget(self._build_sidebar())
        body = QVBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)
        body.addWidget(self._build_topbar())
        body.addWidget(self._build_content(), 1)
        outer.addLayout(body, 1)

        self._center()

    # ---------- topbar ----------
    def _build_topbar(self):
        bar = QFrame()
        bar.setObjectName("adminTopbar")
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(20, 12, 20, 12)

        title = QLabel(RESTAURANT_NAME)
        title.setObjectName("adminTitle")
        sub   = QLabel("Admin Dashboard")
        sub.setObjectName("adminSub")

        lay.addWidget(title)
        lay.addSpacing(8)
        lay.addWidget(sub)
        lay.addStretch()

        now = QLabel(datetime.now().strftime("%A, %d %B %Y"))
        now.setStyleSheet("color:#AAAAAA; font-size:11px;")
        lay.addWidget(now)
        return bar

    # ---------- sidebar ----------
    def _build_sidebar(self):
        panel = QFrame()
        panel.setFixedWidth(190)
        panel.setStyleSheet(f"background:{DARK};")
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        brand = QLabel("ADMIN")
        brand.setStyleSheet(
            f"color:white; font-size:13px; font-weight:bold;"
            f"padding:20px 20px 14px 20px; background:{DARK};")
        lay.addWidget(brand)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background:#444444;")
        sep.setFixedHeight(1)
        lay.addWidget(sep)

        self._nav_group = []
        nav_items = [
            ("Dashboard",       0),
            ("Orders",          1),
            ("Menu",            2),
            ("Customers",       3),
            ("Reports",         4),
            ("Settings",        5),
        ]
        for label, idx in nav_items:
            btn = QPushButton(label)
            btn.setObjectName("nav")
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _, i=idx: self._switch(i))
            self._nav_group.append(btn)
            lay.addWidget(btn)

        self._nav_group[0].setChecked(True)
        lay.addStretch()

        logout_btn = QPushButton("Logout")
        logout_btn.setObjectName("nav")
        logout_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        logout_btn.clicked.connect(self.close)
        lay.addWidget(logout_btn)
        return panel

    # ---------- content ----------
    def _build_content(self):
        self.stack = QStackedWidget()

        self.dash_page     = DashboardPage()
        self.orders_page   = OrdersPage()
        self.menu_page     = MenuPage()
        self.customers_page = CustomersPage()
        self.reports_page  = ReportsPage()
        self.settings_page = SettingsPage()

        for page in (self.dash_page, self.orders_page, self.menu_page,
                     self.customers_page, self.reports_page, self.settings_page):
            self.stack.addWidget(page)

        return self.stack

    # ---------- nav ----------
    def _switch(self, index):
        for i, btn in enumerate(self._nav_group):
            btn.setChecked(i == index)
        self.stack.setCurrentIndex(index)
        refreshable = {0: self.dash_page, 1: self.orders_page,
                       3: self.customers_page, 4: self.reports_page}
        if index in refreshable:
            refreshable[index].refresh()

    def _center(self):
        screen = self.screen() or QApplication.primaryScreen()
        if screen:
            r = screen.availableGeometry()
            self.move(r.x() + (r.width() - self.width()) // 2,
                      r.y() + (r.height() - self.height()) // 2)

    def showEvent(self, event):
        super().showEvent(event)
        if not getattr(self, "_centered", False):
            self._centered = True
            self._center()


# ---------- entry point ----------

def load_roboto_font(app=None):
    font_dir = os.path.dirname(os.path.abspath(__file__))
    for font_file in ("Roboto-Regular.ttf", "Roboto-Bold.ttf"):
        path = os.path.join(font_dir, font_file)
        if os.path.exists(path):
            QFontDatabase.addApplicationFont(path)
    if app:
        app.setFont(QFont("Roboto", 10))


def launch_admin_panel(parent_widget=None):
    app = QApplication.instance()
    if app:
        load_roboto_font(app)
    login_win = AdminLoginWindow(parent_widget)

    def _open_dashboard():
        dashboard = AdminDashboard()
        from gui import STYLE
        if app:
            app.setStyleSheet(STYLE + ADMIN_EXTRA_STYLE)
        dashboard.show()
        login_win._dashboard = dashboard

    login_win.authenticated.connect(_open_dashboard)
    login_win.show()


# ---------- cli setup ----------

def _cli_setup(username=None, password=None):
    print("=== Admin Account Setup ===")
    if not username:
        if admin_exists():
            ans = input("An admin account already exists. Overwrite? [y/N] ").strip().lower()
            if ans != "y":
                print("Aborted.")
                return
        username = input("Admin username: ").strip()
    if not username:
        print("Username cannot be empty.")
        return

    if not password:
        pw  = input("Admin password (min 8 chars): ").strip()
        pw2 = input("Confirm password: ").strip()
        if pw != pw2:
            print("Passwords do not match.")
            return
    else:
        pw = password

    if len(pw) < 8:
        print("Password must be at least 8 characters.")
        return
    _save_admin_creds(username, pw)
    print(f"Admin account '{username}' created. Credentials saved to admin_credentials.json")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--setup", action="store_true",
                        help="Create or reset the admin account")
    parser.add_argument("--username", type=str, default=None,
                        help="Admin username for setup")
    parser.add_argument("--password", type=str, default=None,
                        help="Admin password for setup")
    args = parser.parse_args()

    if args.setup:
        _cli_setup(args.username, args.password)
    else:
        app = QApplication(sys.argv)
        load_roboto_font(app)
        try:
            from gui import STYLE
        except ImportError:
            STYLE = ""
        app.setStyleSheet(STYLE + ADMIN_EXTRA_STYLE)
        login = AdminLoginWindow()

        def _show_dash():
            d = AdminDashboard()
            d.show()
            login._dashboard = d

        login.authenticated.connect(_show_dash)
        login.show()
        sys.exit(app.exec())
