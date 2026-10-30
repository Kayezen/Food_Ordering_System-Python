import os
import sys

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QFontDatabase, QPainter, QPainterPath, QPixmap
from PyQt6.QtWidgets import (
    QApplication, QButtonGroup, QComboBox, QFrame, QGraphicsDropShadowEffect,
    QGridLayout, QHBoxLayout, QLabel, QLineEdit, QMainWindow, QMessageBox,
    QPushButton, QScrollArea, QSizePolicy, QStackedWidget, QVBoxLayout, QWidget,
)

import logic
from menu import CATEGORIES, RESTAURANT_NAME, RESTAURANT_TAGLINE, resolve_image

# ---------- colors ----------
GREEN = "#0DAA5F"
GREEN_DARK = "#098B4C"
DARK = "#2B2B2B"
TEXT = "#333333"
MUTED = "#8A8A8A"
LINE = "#EAEAEA"
BG = "#F3F3F3"
RED = "#D32F2F"

STYLE = f"""
* {{ font-family: 'Roboto', sans-serif; }}
QMainWindow, QWidget#root {{ background-color: {BG}; }}
QLabel {{ color: {TEXT}; }}

/* top bar */
QFrame#topbar {{ background: white; border-bottom: 1px solid {LINE}; }}
QLabel#restaurant {{ font-size: 18px; font-weight: bold; }}
QLabel#tagline {{ color: {MUTED}; font-size: 11px; }}

/* white surfaces */
QFrame#surface {{ background: white; }}

/* category sidebar */
QPushButton#cat {{
    background: white; color: {TEXT}; border: none; border-bottom: 1px solid {LINE};
    border-radius: 0; text-align: left; padding: 15px 16px;
    font-size: 11px; font-weight: bold;
}}
QPushButton#cat:hover {{ background: #FAFAFA; }}
QPushButton#cat:checked {{ background: {GREEN}; color: white; }}

/* search */
QLineEdit, QComboBox {{
    background: white; color: {TEXT}; border: 1px solid {LINE};
    border-radius: 3px; padding: 8px 10px; font-size: 12px;
}}
QLineEdit:focus, QComboBox:focus {{ border: 1px solid {GREEN}; }}
QLineEdit:disabled {{ background: #F7F7F7; color: #BDBDBD; }}
QLineEdit#search {{ background: {BG}; border: none; padding: 10px 12px; }}
QComboBox::drop-down {{ border: none; width: 20px; }}

/* food cards */
QFrame#card {{ background: white; border: 1px solid {LINE}; border-radius: 3px; }}
QLabel#pic {{ background: #F5F5F5; border-radius: 0; }}
QLabel#itemName {{ font-size: 12px; font-weight: bold; }}
QLabel#desc {{ color: {MUTED}; font-size: 10px; }}
QLabel#price {{ color: {GREEN}; font-size: 12px; font-weight: bold; }}

/* buttons */
QPushButton {{
    background: {GREEN}; color: white; border: none; border-radius: 3px;
    padding: 6px 14px; font-size: 11px; font-weight: bold;
}}
QPushButton:hover {{ background: {GREEN_DARK}; }}
QPushButton#add {{ padding: 4px 12px; font-size: 10px; }}
QPushButton#place {{ padding: 12px; font-size: 12px; }}
QPushButton#ghost {{
    background: white; color: {GREEN}; border: 1px solid {GREEN};
}}
QPushButton#ghost:hover {{ background: #F1FBF6; }}
QPushButton#small {{
    background: white; color: {TEXT}; border: 1px solid #DDD; border-radius: 3px;
    padding: 0; min-width: 22px; max-width: 22px; min-height: 22px; max-height: 22px;
    font-size: 13px;
}}
QPushButton#small:hover {{ border-color: {GREEN}; color: {GREEN}; }}
QPushButton#remove {{ background: transparent; color: {MUTED}; padding: 2px 6px; font-size: 12px; }}
QPushButton#remove:hover {{ color: {RED}; background: transparent; }}

/* cart */
QLabel#cartHeader {{
    background: {DARK}; color: white; font-size: 11px; font-weight: bold;
    padding: 15px 16px;
}}
QFrame#cartRow {{ background: white; border: none; border-bottom: 1px solid {LINE}; }}
QLabel#emptyTitle {{ font-size: 13px; font-weight: bold; }}
QLabel#empty {{ color: {MUTED}; font-size: 11px; }}
QLabel#totalLabel, QLabel#totalValue {{ font-size: 14px; font-weight: bold; }}

/* scrolling */
QScrollArea {{ border: none; background: transparent; }}
QScrollArea > QWidget > QWidget {{ background: transparent; }}
QScrollBar:vertical {{ background: transparent; width: 8px; margin: 0; }}
QScrollBar::handle:vertical {{ background: #D5D5D5; border-radius: 4px; min-height: 30px; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}

/* login / sign up window */
QWidget#authBg {{ background-color: #E8ECF4; }}
QLabel#welcome {{ color: white; font-size: 28px; font-weight: bold; }}
QLabel#welcomeText {{ color: white; font-size: 14px; }}
QPushButton#outlineWhite {{
    background: transparent; color: white; border: 1px solid white;
    border-radius: 18px; padding: 8px 28px; font-size: 13px; font-weight: normal;
}}
QPushButton#outlineWhite:hover {{ background: rgba(255, 255, 255, 40); }}
QLabel#authTitle {{ font-size: 22px; color: #555555; }}
QLabel#fieldLabel {{ font-size: 13px; color: #555555; }}
QLineEdit#authInput {{
    background: white; border: 1px solid #DDDDDD; border-radius: 16px;
    padding: 6px 12px; font-size: 12px; min-height: 20px;
}}
QLineEdit#authInput:focus {{ border: 1px solid {GREEN}; }}
QPushButton#authSubmit {{
    background: white; color: {GREEN}; border: 1px solid {GREEN};
    border-radius: 17px; padding: 8px; font-size: 13px; font-weight: normal;
}}
QPushButton#authSubmit:hover {{ background: {GREEN}; color: white; }}
QPushButton#link {{
    background: transparent; color: {GREEN}; border: none; text-align: left;
    padding: 4px 0; font-size: 12px; font-weight: normal;
}}
QPushButton#link:hover {{ color: {GREEN_DARK}; background: transparent; }}
"""

CARD_WIDTH = 205


class PictureLabel(QLabel):

    def __init__(self, path, height):
        super().__init__()
        self._source = QPixmap(path)
        self.setObjectName("pic")
        self.setFixedHeight(height)
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
        self.setMinimumWidth(1)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        w, h = self.width(), self.height()
        if w <= 0 or self._source.isNull():
            return
        scaled = self._source.scaled(
            w, h, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation)
        self.setPixmap(scaled.copy((scaled.width() - w) // 2,
                                   (scaled.height() - h) // 2, w, h))


def clear_layout(layout):
    while layout.count():
        child = layout.takeAt(0)
        if child.widget():
            child.widget().deleteLater()
        elif child.layout():
            clear_layout(child.layout())


class MainWindow(QMainWindow):

    logged_out = pyqtSignal()

    def __init__(self, username=""):
        super().__init__()
        self.username = username
        self.setWindowTitle(RESTAURANT_NAME if "Food Ordering System" in RESTAURANT_NAME else f"{RESTAURANT_NAME} - Food Ordering System")
        self.resize(1060, 680)
        self.setMinimumSize(880, 560)

        self.cart = logic.Cart()
        self.current_category = "All"
        self.columns = 0

        self.build_ui()
        self.refresh_menu()
        self.refresh_cart()
        if username:
            self.name_input.setText(username)

    # ---------- building ----------
    def build_ui(self):
        root = QWidget()
        root.setObjectName("root")
        self.setCentralWidget(root)
        main = QVBoxLayout(root)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)

        main.addWidget(self.build_topbar())

        body = QHBoxLayout()
        body.setContentsMargins(16, 14, 16, 16)
        body.setSpacing(14)
        body.addWidget(self.build_sidebar())
        body.addWidget(self.build_menu_side(), 3)
        body.addWidget(self.build_cart_side(), 2)
        main.addLayout(body, 1)

    def build_topbar(self):
        bar = QFrame()
        bar.setObjectName("topbar")
        outer = QHBoxLayout(bar)
        outer.setContentsMargins(20, 12, 20, 12)

        left = QVBoxLayout()
        left.setSpacing(0)
        title = QLabel(RESTAURANT_NAME)
        title.setObjectName("restaurant")
        tagline = QLabel(RESTAURANT_TAGLINE)
        tagline.setObjectName("tagline")
        left.addWidget(title)
        left.addWidget(tagline)
        outer.addLayout(left)
        outer.addStretch()

        if self.username:
            hello = QLabel(f"Hi, {self.username}")
            hello.setStyleSheet(f"color:{MUTED}; font-size:12px;")
            logout = QPushButton("Log Out")
            logout.setObjectName("ghost")
            logout.setCursor(Qt.CursorShape.PointingHandCursor)
            logout.clicked.connect(self.on_logout)
            outer.addWidget(hello)
            outer.addSpacing(10)
            outer.addWidget(logout)
        return bar

    def build_sidebar(self):
        side = QFrame()
        side.setObjectName("surface")
        side.setFixedWidth(160)
        layout = QVBoxLayout(side)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.category_group = QButtonGroup(self)
        self.category_group.setExclusive(True)
        for name in CATEGORIES:
            btn = QPushButton(name.upper())
            btn.setObjectName("cat")
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            if name == "All":
                btn.setChecked(True)
            btn.clicked.connect(lambda checked=False, c=name: self.on_category(c))
            self.category_group.addButton(btn)
            layout.addWidget(btn)
        layout.addStretch()
        return side

    def build_menu_side(self):
        surface = QFrame()
        surface.setObjectName("surface")
        layout = QVBoxLayout(surface)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        self.search_box = QLineEdit()
        self.search_box.setObjectName("search")
        self.search_box.setPlaceholderText("Search")
        self.search_box.setClearButtonEnabled(True)
        self.search_box.textChanged.connect(self.refresh_menu)
        layout.addWidget(self.search_box)

        self.menu_scroll = QScrollArea()
        self.menu_scroll.setWidgetResizable(True)
        self.menu_container = QWidget()
        self.menu_grid = QGridLayout(self.menu_container)
        self.menu_grid.setSpacing(12)
        self.menu_grid.setContentsMargins(0, 0, 4, 0)
        self.menu_scroll.setWidget(self.menu_container)
        layout.addWidget(self.menu_scroll, 1)
        return surface

    def build_cart_side(self):
        panel = QFrame()
        panel.setObjectName("surface")
        panel.setMinimumWidth(320)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QLabel("YOUR CART")
        header.setObjectName("cartHeader")
        layout.addWidget(header)

        body = QVBoxLayout()
        body.setContentsMargins(14, 8, 14, 14)
        body.setSpacing(6)
        layout.addLayout(body, 1)

        self.cart_scroll = QScrollArea()
        self.cart_scroll.setWidgetResizable(True)
        self.cart_container = QWidget()
        self.cart_layout = QVBoxLayout(self.cart_container)
        self.cart_layout.setSpacing(0)
        self.cart_layout.setContentsMargins(0, 0, 0, 0)
        self.cart_scroll.setWidget(self.cart_container)
        body.addWidget(self.cart_scroll, 1)

        self.subtotal_value = QLabel()
        self.fee_value = QLabel()
        self.total_value = QLabel()
        self.total_value.setObjectName("totalValue")
        body.addLayout(self.summary_row("Subtotal", self.subtotal_value))
        body.addLayout(self.summary_row("Delivery fee", self.fee_value))
        total_label = QLabel("Total")
        total_label.setObjectName("totalLabel")
        total_row = QHBoxLayout()
        total_row.addWidget(total_label)
        total_row.addStretch()
        total_row.addWidget(self.total_value)
        body.addLayout(total_row)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Customer name *")
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("Contact number *")
        self.type_combo = QComboBox()
        self.type_combo.addItems(logic.ORDER_TYPES)
        self.type_combo.currentTextChanged.connect(self.on_order_type_changed)
        self.payment_combo = QComboBox()
        self.payment_combo.addItems(logic.PAYMENT_METHODS)
        self.address_input = QLineEdit()
        self.address_input.setPlaceholderText("Delivery address (Delivery only)")
        self.address_input.setEnabled(False)
        self.notes_input = QLineEdit()
        self.notes_input.setPlaceholderText("Order notes (optional)")

        body.addSpacing(4)
        body.addWidget(self.name_input)
        body.addWidget(self.phone_input)
        row = QHBoxLayout()
        row.addWidget(self.type_combo)
        row.addWidget(self.payment_combo)
        body.addLayout(row)
        body.addWidget(self.address_input)
        body.addWidget(self.notes_input)

        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        body.addWidget(self.status_label)

        self.place_button = QPushButton("PLACE ORDER")
        self.place_button.setObjectName("place")
        self.place_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.place_button.clicked.connect(self.on_place_order)
        body.addWidget(self.place_button)

        clear_btn = QPushButton("Clear Cart")
        clear_btn.setObjectName("ghost")
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.clicked.connect(self.on_clear_cart)
        body.addWidget(clear_btn)
        return panel

    def summary_row(self, text, value_label):
        row = QHBoxLayout()
        label = QLabel(text)
        label.setStyleSheet(f"color:{MUTED}; font-size:12px;")
        value_label.setStyleSheet("font-size:12px;")
        row.addWidget(label)
        row.addStretch()
        row.addWidget(value_label)
        return row

    # ---------- menu display ----------
    def refresh_menu(self):
        items = logic.filter_menu(self.search_box.text(), self.current_category)
        clear_layout(self.menu_grid)

        if not items:
            msg = QLabel("No food items found.")
            msg.setObjectName("empty")
            msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.menu_grid.addWidget(msg, 0, 0)
            return

        width = self.menu_scroll.viewport().width()
        self.columns = max(1, width // (CARD_WIDTH + 12))
        for index, item in enumerate(items):
            row, col = divmod(index, self.columns)
            self.menu_grid.addWidget(self.make_food_card(item), row, col)
        for col in range(self.columns):
            self.menu_grid.setColumnStretch(col, 1)
        self.menu_grid.setRowStretch(len(items) // self.columns + 1, 1)

    def make_food_card(self, item):
        card = QFrame()
        card.setObjectName("card")
        card.setMinimumWidth(CARD_WIDTH)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        image_path = resolve_image(item.get("image"))
        if image_path:
            pic = PictureLabel(image_path, 110)
        else:
            pic = QLabel(item.get("category", "").upper())
            pic.setObjectName("pic")
            pic.setAlignment(Qt.AlignmentFlag.AlignCenter)
            pic.setFixedHeight(110)
            pic.setStyleSheet(f"background: #F5F5F5; color: {MUTED}; font-size: 11px; font-weight: bold; letter-spacing: 1px;")
        layout.addWidget(pic)

        name = QLabel(item["name"])
        name.setObjectName("itemName")
        name.setWordWrap(True)
        desc = QLabel(item["description"])
        desc.setObjectName("desc")
        desc.setWordWrap(True)
        layout.addWidget(name)
        layout.addWidget(desc)
        layout.addStretch()

        bottom = QHBoxLayout()
        price = QLabel(logic.format_price(item["price"]))
        price.setObjectName("price")
        add_btn = QPushButton("ADD")
        add_btn.setObjectName("add")
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.clicked.connect(lambda checked=False, i=item["id"]: self.on_add(i))
        bottom.addWidget(price)
        bottom.addStretch()
        bottom.addWidget(add_btn)
        layout.addLayout(bottom)
        return card

    # ---------- cart display ----------
    def refresh_cart(self):
        summary = logic.get_summary(self.cart, self.type_combo.currentText())
        clear_layout(self.cart_layout)

        if summary["is_empty"]:
            self.cart_layout.addStretch()
            title = QLabel("Your cart is empty")
            title.setObjectName("emptyTitle")
            title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            hint = QLabel("Add items to start ordering")
            hint.setObjectName("empty")
            hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.cart_layout.addWidget(title)
            self.cart_layout.addWidget(hint)
        else:
            for line in summary["lines"]:
                self.cart_layout.addWidget(self.make_cart_row(line))
        self.cart_layout.addStretch()

        self.subtotal_value.setText(logic.format_price(summary["subtotal"]))
        self.fee_value.setText(logic.format_price(summary["delivery_fee"]))
        self.total_value.setText(logic.format_price(summary["total"]))

    def make_cart_row(self, line):
        row = QFrame()
        row.setObjectName("cartRow")
        layout = QVBoxLayout(row)
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(4)

        top = QHBoxLayout()
        name = QLabel(line["name"])
        name.setObjectName("itemName")
        name.setWordWrap(True)
        remove = QPushButton("✕")
        remove.setObjectName("remove")
        remove.setToolTip("Remove from cart")
        remove.setCursor(Qt.CursorShape.PointingHandCursor)
        remove.clicked.connect(lambda checked=False, i=line["id"]: self.on_remove(i))
        top.addWidget(name, 1)
        top.addWidget(remove)
        layout.addLayout(top)

        bottom = QHBoxLayout()
        minus = QPushButton("−")
        minus.setObjectName("small")
        minus.clicked.connect(lambda checked=False, i=line["id"]: self.on_decrease(i))
        qty = QLabel(str(line["quantity"]))
        qty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        qty.setMinimumWidth(26)
        plus = QPushButton("+")
        plus.setObjectName("small")
        plus.clicked.connect(lambda checked=False, i=line["id"]: self.on_increase(i))
        sub = QLabel(logic.format_price(line["subtotal"]))
        sub.setObjectName("price")
        bottom.addWidget(minus)
        bottom.addWidget(qty)
        bottom.addWidget(plus)
        bottom.addStretch()
        bottom.addWidget(sub)
        layout.addLayout(bottom)
        return row

    # ---------- event handlers ----------
    def on_logout(self):
        self.logged_out.emit()
        self.close()

    def on_category(self, category):
        self.current_category = category
        self.refresh_menu()

    def on_add(self, item_id):
        self.cart.add_item(item_id)
        self.set_status("")
        self.refresh_cart()

    def on_increase(self, item_id):
        self.cart.increase_item(item_id)
        self.refresh_cart()

    def on_decrease(self, item_id):
        self.cart.decrease_item(item_id)
        self.refresh_cart()

    def on_remove(self, item_id):
        self.cart.remove_item(item_id)
        self.refresh_cart()

    def on_clear_cart(self):
        self.cart.clear()
        self.set_status("")
        self.refresh_cart()

    def on_order_type_changed(self, order_type):
        self.address_input.setEnabled(order_type == "Delivery")
        if order_type != "Delivery":
            self.address_input.clear()
        self.refresh_cart()

    def on_place_order(self):
        result = logic.place_order(
            self.cart,
            self.name_input.text(),
            self.phone_input.text(),
            self.type_combo.currentText(),
            self.address_input.text(),
            self.payment_combo.currentText(),
            self.notes_input.text(),
        )

        if not result["success"]:
            text = "\n".join(f"• {e}" for e in result["errors"])
            self.set_status(text, error=True)
            QMessageBox.warning(self, "Cannot place order", text)
            return

        order = result["order"]
        self.set_status(f"Order {order['order_number']} placed successfully!")
        QMessageBox.information(
            self, "Order Confirmed",
            "Thank you for your order!\n\n" + logic.format_order_confirmation(order))

        for box in (self.name_input, self.phone_input,
                    self.address_input, self.notes_input):
            box.clear()
        self.type_combo.setCurrentIndex(0)
        self.payment_combo.setCurrentIndex(0)
        self.refresh_cart()

    # ---------- utilities ----------
    def set_status(self, text, error=False):
        color = RED if error else GREEN
        self.status_label.setStyleSheet(f"color:{color}; font-size:11px; font-weight:bold;")
        self.status_label.setText(text)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        QTimer.singleShot(0, self.relayout_if_needed)

    def relayout_if_needed(self):
        width = self.menu_scroll.viewport().width()
        columns = max(1, width // (CARD_WIDTH + 12))
        if columns != self.columns:
            self.refresh_menu()

    def center_on_screen(self):
        screen = self.screen() or QApplication.primaryScreen()
        if screen:
            rect = screen.availableGeometry()
            self.move(
                rect.x() + max(0, (rect.width() - self.width()) // 2),
                rect.y() + max(0, (rect.height() - self.height()) // 2),
            )

    def showEvent(self, event):
        super().showEvent(event)
        if not getattr(self, "_already_centered", False):
            self._already_centered = True
            self.center_on_screen()
        QTimer.singleShot(0, self.relayout_if_needed)


class AuthCard(QWidget):

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor("white"))
        w, h = self.width(), self.height()
        triangle = QPainterPath()
        triangle.moveTo(0, 0)
        triangle.lineTo(w * 0.6, 0)
        triangle.lineTo(0, h)
        triangle.closeSubpath()
        painter.fillPath(triangle, QColor(GREEN))
        painter.end()


class AuthWindow(QWidget):

    logged_in = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setObjectName("authBg")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setWindowTitle(f"{RESTAURANT_NAME} - Sign In")
        self.resize(940, 640)
        self.setMinimumSize(820, 560)
        self.mode = "login"

        outer = QVBoxLayout(self)
        self.card = AuthCard()
        self.card.setFixedSize(760, 480)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(25)
        shadow.setOffset(0, 3)
        shadow.setColor(QColor(0, 0, 0, 60))
        self.card.setGraphicsEffect(shadow)
        outer.addWidget(self.card, alignment=Qt.AlignmentFlag.AlignCenter)

        row = QHBoxLayout(self.card)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(0)
        row.addWidget(self.build_left())
        row.addWidget(self.build_right(), 1)
        self.set_mode("login")

    def center_on_screen(self):
        screen = self.screen() or QApplication.primaryScreen()
        if screen:
            rect = screen.availableGeometry()
            self.move(
                rect.x() + max(0, (rect.width() - self.width()) // 2),
                rect.y() + max(0, (rect.height() - self.height()) // 2),
            )

    def showEvent(self, event):
        super().showEvent(event)
        if not getattr(self, "_already_centered", False):
            self._already_centered = True
            self.center_on_screen()

    # ---------- building ----------
    def build_left(self):
        left = QWidget()
        left.setFixedWidth(380)
        layout = QVBoxLayout(left)
        layout.setContentsMargins(36, 50, 0, 0)
        layout.setSpacing(12)

        self.welcome_title = QLabel()
        self.welcome_title.setObjectName("welcome")
        self.welcome_text = QLabel()
        self.welcome_text.setObjectName("welcomeText")
        self.welcome_text.setWordWrap(True)
        self.welcome_text.setFixedWidth(200)
        self.switch_button = QPushButton()
        self.switch_button.setObjectName("outlineWhite")
        self.switch_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.switch_button.clicked.connect(self.on_switch)

        layout.addWidget(self.welcome_title)
        layout.addWidget(self.welcome_text)
        layout.addSpacing(6)
        layout.addWidget(self.switch_button, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addStretch()
        return left

    def build_right(self):
        right = QWidget()
        layout = QVBoxLayout(right)
        layout.setContentsMargins(38, 40, 42, 0)

        admin_row = QHBoxLayout()
        admin_row.addStretch()
        admin_icon_btn = QPushButton("⚙")
        admin_icon_btn.setObjectName("small")
        admin_icon_btn.setToolTip("Administrator Access")
        admin_icon_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        admin_icon_btn.clicked.connect(self._open_admin_login)
        admin_row.addWidget(admin_icon_btn)
        layout.addLayout(admin_row)

        self.stack = QStackedWidget()

        self.login_page, self.login_fields, login_btn, self.login_status = \
            self.make_form("Login", [
                ("Username/Email address", "Username or Email", False),
                ("Password", "Password", True)], "Sign In")
        login_btn.clicked.connect(self.on_login)
        forgot = QPushButton("Forgot password?")
        forgot.setObjectName("link")
        forgot.setCursor(Qt.CursorShape.PointingHandCursor)
        forgot.clicked.connect(lambda: self.set_mode("reset"))
        self.login_page.layout().addWidget(forgot, alignment=Qt.AlignmentFlag.AlignLeft)

        self.signup_page, self.signup_fields, signup_btn, self.signup_status = \
            self.make_form("Sign Up", [
                ("Username", "Choose a username", False),
                ("Email address", "you@example.com", False),
                ("Password", "At least 6 characters", True),
                ("Confirm password", "Re-enter password", True)], "Sign Up")
        signup_btn.clicked.connect(self.on_signup)

        self.reset_page, self.reset_fields, reset_btn, self.reset_status = \
            self.make_form("Reset Password", [
                ("Username/Email address", "Username or Email", False),
                ("Recovery code", "e.g. K7QM-X2RD-9TPA", False),
                ("New password", "At least 6 characters", True),
                ("Confirm new password", "Re-enter password", True)], "Reset Password")
        reset_btn.clicked.connect(self.on_reset)
        back_reset = QPushButton("Back to login")
        back_reset.setObjectName("link")
        back_reset.setCursor(Qt.CursorShape.PointingHandCursor)
        back_reset.clicked.connect(lambda: self.set_mode("login"))
        self.reset_page.layout().addWidget(back_reset, alignment=Qt.AlignmentFlag.AlignLeft)

        self.admin_page, self.admin_fields, admin_btn, self.admin_status = \
            self.make_form("Administrator Login", [
                ("Username", "Admin username", False),
                ("Password", "Password", True)], "Sign In")
        admin_btn.clicked.connect(self.on_admin_login)
        pw_box  = self.admin_fields[1]
        eye_btn = QPushButton("Show")
        eye_btn.setObjectName("ghost")
        eye_btn.setFixedHeight(28)
        eye_btn.setToolTip("Show / hide password")
        eye_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        eye_btn.setCheckable(True)
        def _toggle_pw(on):
            pw_box.setEchoMode(QLineEdit.EchoMode.Normal if on else QLineEdit.EchoMode.Password)
            eye_btn.setText("Hide" if on else "Show")
        eye_btn.toggled.connect(_toggle_pw)
        a_lay = self.admin_page.layout()
        for i in range(a_lay.count()):
            if a_lay.itemAt(i) and a_lay.itemAt(i).widget() is pw_box:
                a_lay.removeWidget(pw_box)
                pw_row = QWidget()
                pw_row_lay = QHBoxLayout(pw_row)
                pw_row_lay.setContentsMargins(0, 0, 0, 0)
                pw_row_lay.setSpacing(6)
                pw_row_lay.addWidget(pw_box, 1)
                pw_row_lay.addWidget(eye_btn)
                a_lay.insertWidget(i, pw_row)
                break
        back_admin = QPushButton("Back to login")
        back_admin.setObjectName("link")
        back_admin.setCursor(Qt.CursorShape.PointingHandCursor)
        back_admin.clicked.connect(lambda: self.set_mode("login"))
        self.admin_page.layout().addWidget(back_admin, alignment=Qt.AlignmentFlag.AlignLeft)

        for page in (self.login_page, self.signup_page, self.reset_page, self.admin_page):
            self.stack.addWidget(page)
        layout.addWidget(self.stack)
        layout.addStretch()
        return right

    def make_form(self, title, fields, button_text):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        heading = QLabel(title)
        heading.setObjectName("authTitle")
        layout.addWidget(heading)
        layout.addSpacing(8)

        inputs = []
        for label_text, placeholder, is_password in fields:
            label = QLabel(f"{label_text}<span style='color:#E53935;'>*</span>")
            label.setTextFormat(Qt.TextFormat.RichText)
            label.setObjectName("fieldLabel")
            box = QLineEdit()
            box.setObjectName("authInput")
            box.setPlaceholderText(placeholder)
            if is_password:
                box.setEchoMode(QLineEdit.EchoMode.Password)
            layout.addWidget(label)
            layout.addWidget(box)
            layout.addSpacing(6)
            inputs.append(box)

        button = QPushButton(button_text)
        button.setObjectName("authSubmit")
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(button)

        status = QLabel("")
        status.setWordWrap(True)
        layout.addWidget(status)

        inputs[-1].returnPressed.connect(button.click)
        return page, inputs, button, status

    # ---------- behaviour ----------
    def _open_admin_login(self):
        self.set_mode("admin")

    def set_mode(self, mode):
        self.mode = mode
        pages = {
            "login":  self.login_page,
            "signup": self.signup_page,
            "reset":  self.reset_page,
            "admin":  self.admin_page,
        }
        self.stack.setCurrentWidget(pages[mode])
        for label in (self.login_status, self.signup_status,
                      self.reset_status, self.admin_status):
            label.setText("")

        if mode == "signup":
            self.welcome_title.setText("Welcome Back!")
            self.welcome_text.setText("Already have an account?\nSign in here.")
            self.switch_button.setText("Sign In")
            self.switch_button.show()
        elif mode == "admin":
            self.welcome_title.setText("Admin\nAccess")
            self.welcome_text.setText("Restricted area.\nAuthorised personnel only.")
            self.switch_button.setText("← Back to Login")
            self.switch_button.show()
        else:
            self.welcome_title.setText("Welcome!")
            self.welcome_text.setText("Create your account.\nFor Free!")
            self.switch_button.setText("Sign Up")
            self.switch_button.show()

    def on_switch(self):
        if self.mode in ("reset", "admin"):
            self.set_mode("login")
        elif self.mode == "signup":
            self.set_mode("login")
        else:
            self.set_mode("signup")

    def show_status(self, label, text, error=True):
        color = RED if error else GREEN
        label.setStyleSheet(f"color:{color}; font-size:11px;")
        label.setText(text)

    def on_login(self):
        ok, message, username = logic.login_user(
            self.login_fields[0].text(), self.login_fields[1].text())
        if ok:
            self.login_fields[1].clear()
            code = logic.issue_recovery_code_if_missing(username)
            if code:
                self.show_recovery_code(code)
            self.logged_in.emit(username)
        else:
            self.show_status(self.login_status, message)

    def on_signup(self):
        values = [box.text() for box in self.signup_fields]
        ok, message, recovery_code = logic.register_user(*values)
        if not ok:
            self.show_status(self.signup_status, message)
            return
        self.show_recovery_code(recovery_code)
        for box in self.signup_fields:
            box.clear()
        self.set_mode("login")
        self.login_fields[0].setText(values[0])
        self.login_fields[1].setFocus()
        self.show_status(self.login_status, message, error=False)

    def on_reset(self):
        values = [box.text() for box in self.reset_fields]
        ok, message, new_code = logic.reset_password(*values)
        if not ok:
            self.show_status(self.reset_status, message)
            return
        for box in self.reset_fields:
            box.clear()
        self.show_recovery_code(new_code, replaced=True)
        self.set_mode("login")
        self.login_fields[0].setText(values[0])
        self.show_status(self.login_status, message, error=False)

    def show_recovery_code(self, code, replaced=False):
        extra = ("Your old code no longer works. Here is your new one.\n\n"
                 if replaced else "")
        QMessageBox.information(
            self, "Save your recovery code",
            f"{extra}Recovery code:\n\n        {code}\n\n"
            "Write it down or keep it somewhere safe. You will need it if you "
            "ever forget your password, and it will not be shown again.")

    def on_admin_login(self):
        import admingui
        username = self.admin_fields[0].text()
        password = self.admin_fields[1].text()
        if not admingui.admin_exists():
            self.show_status(self.admin_status,
                             "No admin account. Run: python admingui.py --setup")
            return
        if admingui.verify_admin(username, password):
            self.admin_fields[1].clear()
            dashboard = admingui.AdminDashboard()
            try:
                QApplication.instance().setStyleSheet(
                    STYLE + admingui.ADMIN_EXTRA_STYLE)
            except Exception:
                pass
            dashboard.show()
            self._admin_dashboard = dashboard
            self.close()
        else:
            self.show_status(self.admin_status, "Incorrect username or password.")


class AppController:

    def __init__(self):
        self.auth = None
        self.main = None

    def show_auth(self):
        self.auth = AuthWindow()
        self.auth.logged_in.connect(self.show_main)
        self.auth.show()

    def show_main(self, username):
        self.main = MainWindow(username)
        self.main.logged_out.connect(self.show_auth)
        self.main.show()
        if self.auth:
            self.auth.close()


def load_roboto_font(app):
    font_dir = os.path.dirname(os.path.abspath(__file__))
    for font_file in ("Roboto-Regular.ttf", "Roboto-Bold.ttf"):
        path = os.path.join(font_dir, font_file)
        if os.path.exists(path):
            QFontDatabase.addApplicationFont(path)
    app.setFont(QFont("Roboto", 10))


def main():
    app = QApplication(sys.argv)
    load_roboto_font(app)
    app.setStyleSheet(STYLE)
    controller = AppController()
    controller.show_auth()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
