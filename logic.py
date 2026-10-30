import hashlib
import hmac
import json
import os
import re
import secrets
from datetime import datetime

from menu import get_all_items

# ---------- constants ----------
PESO = "₱"
DELIVERY_FEE = 50.00
ORDER_TYPES = ["Dine-in", "Takeout", "Delivery"]
PAYMENT_METHODS = ["Cash", "GCash", "Credit/Debit Card"]

ORDERS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "admin_orders.json")


# ---------- order storage ----------
def load_orders():
    if not os.path.exists(ORDERS_FILE):
        return []
    try:
        with open(ORDERS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        os.replace(ORDERS_FILE, f"{ORDERS_FILE}.corrupt-{stamp}")
        return []


def save_orders(orders):
    tmp = ORDERS_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(orders, f, indent=2, ensure_ascii=False)
    os.replace(tmp, ORDERS_FILE)


def _next_order_number(orders):
    highest = 0
    for o in orders:
        m = re.fullmatch(r"FO-(\d+)", str(o.get("order_number", "")))
        if m:
            highest = max(highest, int(m.group(1)))
    return f"FO-{highest + 1:04d}"


def format_price(amount):
    return f"{PESO}{amount:,.2f}"


# ---------- search / filter ----------
def get_item(item_id):
    for item in get_all_items():
        if item["id"] == item_id:
            return item
    return None


def filter_menu(search_text="", category="All"):
    search_text = search_text.strip().lower()
    results = []
    for item in get_all_items():
        if category != "All" and item["category"] != category:
            continue
        if search_text and search_text not in item["name"].lower():
            continue
        results.append(item)
    return results


# ---------- cart ----------
class Cart:

    def __init__(self):
        self._quantities = {}

    def add_item(self, item_id):
        if get_item(item_id) is None:
            return
        self._quantities[item_id] = self._quantities.get(item_id, 0) + 1

    def increase_item(self, item_id):
        self.add_item(item_id)

    def decrease_item(self, item_id):
        if item_id in self._quantities:
            self._quantities[item_id] -= 1
            if self._quantities[item_id] <= 0:
                del self._quantities[item_id]

    def remove_item(self, item_id):
        self._quantities.pop(item_id, None)

    def clear(self):
        self._quantities.clear()

    def is_empty(self):
        return len(self._quantities) == 0

    def item_count(self):
        return sum(self._quantities.values())

    def get_lines(self):
        lines = []
        for item_id, qty in self._quantities.items():
            item = get_item(item_id)
            lines.append({
                "id": item_id,
                "name": item["name"],
                "price": item["price"],
                "quantity": qty,
                "subtotal": item["price"] * qty,
            })
        return lines

    def subtotal(self):
        return sum(line["subtotal"] for line in self.get_lines())


# ---------- totals ----------
def get_delivery_fee(order_type):
    return DELIVERY_FEE if order_type == "Delivery" else 0.0


def get_summary(cart, order_type="Dine-in"):
    subtotal = cart.subtotal()
    fee = get_delivery_fee(order_type) if not cart.is_empty() else 0.0
    return {
        "lines": cart.get_lines(),
        "item_count": cart.item_count(),
        "subtotal": subtotal,
        "delivery_fee": fee,
        "total": subtotal + fee,
        "is_empty": cart.is_empty(),
    }


# ---------- validation ----------
def validate_customer(name, phone, order_type, address):
    errors = []

    name = name.strip()
    if not name:
        errors.append("Customer name is required.")
    elif len(name) < 2:
        errors.append("Customer name must be at least 2 characters.")

    digits = re.sub(r"[\s\-+()]", "", phone.strip())
    if not phone.strip():
        errors.append("Contact number is required.")
    elif not digits.isdigit() or not (7 <= len(digits) <= 13):
        errors.append("Contact number must contain 7 to 13 digits.")

    if order_type == "Delivery" and not address.strip():
        errors.append("Delivery address is required for Delivery orders.")

    return errors


# ---------- order ----------
def place_order(cart, name, phone, order_type, address, payment, notes=""):
    errors = []
    if cart.is_empty():
        errors.append("Your cart is empty. Please add some food first.")
    errors += validate_customer(name, phone, order_type, address)
    if errors:
        return {"success": False, "errors": errors}

    summary = get_summary(cart, order_type)
    try:
        orders = load_orders()
    except OSError:
        return {"success": False,
                "errors": ["Could not read the saved orders. Please try again."]}
    order = {
        "order_number": _next_order_number(orders),
        "time": datetime.now().strftime("%Y-%m-%d %I:%M %p"),
        "customer": name.strip(),
        "phone": phone.strip(),
        "order_type": order_type,
        "address": address.strip() if order_type == "Delivery" else "",
        "payment": payment,
        "notes": notes.strip(),
        "lines": summary["lines"],
        "subtotal": summary["subtotal"],
        "delivery_fee": summary["delivery_fee"],
        "total": summary["total"],
        "status": "Pending",
    }

    try:
        orders.append(order)
        save_orders(orders)
    except OSError:
        return {"success": False,
                "errors": ["Your order could not be saved. Please try again."]}

    cart.clear()
    return {"success": True, "order": order}


def format_order_confirmation(order):
    lines = [f"Order No: {order['order_number']}",
             f"Time: {order['time']}",
             f"Customer: {order['customer']}  ({order['phone']})",
             f"Type: {order['order_type']}   Payment: {order['payment']}"]
    if order["address"]:
        lines.append(f"Address: {order['address']}")
    if order["notes"]:
        lines.append(f"Notes: {order['notes']}")
    lines.append("")
    for line in order["lines"]:
        lines.append(f"{line['quantity']} x {line['name']}  -  "
                     f"{format_price(line['subtotal'])}")
    lines.append("")
    lines.append(f"Subtotal: {format_price(order['subtotal'])}")
    if order["delivery_fee"]:
        lines.append(f"Delivery fee: {format_price(order['delivery_fee'])}")
    lines.append(f"TOTAL: {format_price(order['total'])}")
    return "\n".join(lines)


# ---------- accounts ----------
ACCOUNTS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "accounts.txt")
EMAIL_PATTERN = re.compile(r"^[^@\s|]+@[^@\s|]+\.[^@\s|]+$")
USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_]{3,20}$")
MIN_PASSWORD_LENGTH = 6


def _hash_password(password, salt_hex):
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"),
                               bytes.fromhex(salt_hex), 100_000).hex()


def _new_recovery_code():
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    raw = "".join(secrets.choice(alphabet) for _ in range(12))
    return "-".join(raw[i:i + 4] for i in range(0, 12, 4))


def _normalize_code(code):
    return re.sub(r"[^A-Za-z0-9]", "", code).upper()


def _set_recovery_code(acc):
    code = _new_recovery_code()
    acc["rsalt"] = secrets.token_hex(16)
    acc["rhash"] = _hash_password(_normalize_code(code), acc["rsalt"])
    return code


def load_accounts():
    accounts = []
    if not os.path.exists(ACCOUNTS_FILE):
        return accounts
    with open(ACCOUNTS_FILE, "r", encoding="utf-8") as file:
        for line in file:
            parts = line.strip().split("|")
            if len(parts) in (4, 6):
                acc = {"username": parts[0], "email": parts[1],
                       "salt": parts[2], "hash": parts[3],
                       "rsalt": "", "rhash": ""}
                if len(parts) == 6:
                    acc["rsalt"], acc["rhash"] = parts[4], parts[5]
                accounts.append(acc)
    return accounts


def save_accounts(accounts):
    tmp = ACCOUNTS_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as file:
        for acc in accounts:
            file.write(f"{acc['username']}|{acc['email']}|{acc['salt']}|"
                       f"{acc['hash']}|{acc.get('rsalt', '')}|"
                       f"{acc.get('rhash', '')}\n")
    os.replace(tmp, ACCOUNTS_FILE)


def find_account(identifier, accounts):
    identifier = identifier.strip().lower()
    for acc in accounts:
        if identifier in (acc["username"].lower(), acc["email"].lower()):
            return acc
    return None


def register_user(username, email, password, confirm):
    username, email = username.strip(), email.strip()
    if not username or not email or not password or not confirm:
        return False, "Please fill in all fields.", ""
    if not USERNAME_PATTERN.match(username):
        return False, "Username must be 3-20 letters, numbers or underscores.", ""
    if not EMAIL_PATTERN.match(email):
        return False, "Please enter a valid email address.", ""
    if len(password) < MIN_PASSWORD_LENGTH:
        return False, f"Password must be at least {MIN_PASSWORD_LENGTH} characters.", ""
    if password != confirm:
        return False, "Passwords do not match.", ""

    accounts = load_accounts()
    if find_account(username, accounts):
        return False, "That username is already taken.", ""
    if find_account(email, accounts):
        return False, "That email is already registered.", ""

    salt = secrets.token_hex(16)
    acc = {"username": username, "email": email, "salt": salt,
           "hash": _hash_password(password, salt), "rsalt": "", "rhash": ""}
    code = _set_recovery_code(acc)
    accounts.append(acc)
    save_accounts(accounts)
    return True, "Account created! You can now sign in.", code


def login_user(identifier, password):
    if not identifier.strip() or not password:
        return False, "Please enter your username/email and password.", ""
    acc = find_account(identifier, load_accounts())
    if acc is not None:
        attempt = _hash_password(password, acc["salt"])
        if hmac.compare_digest(attempt, acc["hash"]):
            return True, "Login successful.", acc["username"]
    return False, "Incorrect username/email or password.", ""


def issue_recovery_code_if_missing(username):
    accounts = load_accounts()
    acc = find_account(username, accounts)
    if acc is None or acc.get("rhash"):
        return ""
    code = _set_recovery_code(acc)
    save_accounts(accounts)
    return code


def reset_password(identifier, recovery_code, new_password, confirm):
    if not identifier.strip() or not recovery_code.strip() \
            or not new_password or not confirm:
        return False, "Please fill in all fields.", ""
    if len(new_password) < MIN_PASSWORD_LENGTH:
        return False, f"Password must be at least {MIN_PASSWORD_LENGTH} characters.", ""
    if new_password != confirm:
        return False, "Passwords do not match.", ""

    accounts = load_accounts()
    acc = find_account(identifier, accounts)
    ok = False
    if acc is not None and acc.get("rhash"):
        attempt = _hash_password(_normalize_code(recovery_code), acc["rsalt"])
        ok = hmac.compare_digest(attempt, acc["rhash"])
    if not ok:
        return False, "Incorrect username/email or recovery code.", ""

    acc["salt"] = secrets.token_hex(16)
    acc["hash"] = _hash_password(new_password, acc["salt"])
    new_code = _set_recovery_code(acc)
    save_accounts(accounts)
    return True, "Password updated. You can now sign in.", new_code
