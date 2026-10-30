import copy
import json
import os
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(BASE_DIR, "images")
MENU_FILE = os.path.join(BASE_DIR, "menu.json")

RESTAURANT_NAME = "Food Ordering System"
RESTAURANT_TAGLINE = "Fresh Filipino favorites, made to order."

CATEGORIES = ["All", "Meals", "Burgers", "Snacks", "Drinks"]

_DEFAULT_ITEMS = [
    # ---------- meals ----------
    {"id": 1, "name": "Chicken Adobo Rice Meal",
     "description": "Tender chicken simmered in soy-vinegar sauce with steamed rice.",
     "category": "Meals", "price": 149.00, "image": "images/chicken_adobo.jpg"},
    {"id": 2, "name": "Pork Sinigang",
     "description": "Sour tamarind soup with pork, vegetables and rice.",
     "category": "Meals", "price": 169.00, "image": "images/pork_sinigang.jpg"},
    {"id": 3, "name": "Beef Tapsilog",
     "description": "Marinated beef tapa with garlic rice and a fried egg.",
     "category": "Meals", "price": 159.00, "image": "images/beef_tapsilog.jpg"},
    {"id": 4, "name": "Crispy Pork Sisig",
     "description": "Sizzling chopped pork with onions, chili and calamansi.",
     "category": "Meals", "price": 179.00, "image": "images/pork_sisig.jpg"},
    # ---------- burgers ----------
    {"id": 5, "name": "Classic Cheeseburger",
     "description": "Juicy beef patty, cheddar, lettuce, tomato and house sauce.",
     "category": "Burgers", "price": 129.00, "image": "images/cheeseburger.jpg"},
    {"id": 6, "name": "Double Bacon Burger",
     "description": "Two beef patties stacked with crispy bacon and cheese.",
     "category": "Burgers", "price": 199.00, "image": "images/double_bacon_burger.jpg"},
    {"id": 7, "name": "Chicken Burger",
     "description": "Crispy fried chicken fillet with mayo and pickles.",
     "category": "Burgers", "price": 119.00, "image": "images/chicken_burger.jpg"},
    # ---------- snacks ----------
    {"id": 8, "name": "French Fries",
     "description": "Golden, crispy and lightly salted.",
     "category": "Snacks", "price": 69.00, "image": "images/french_fries.jpg"},
    {"id": 9, "name": "Lumpiang Shanghai (8 pcs)",
     "description": "Crispy pork spring rolls with sweet chili sauce.",
     "category": "Snacks", "price": 89.00, "image": "images/lumpiang_shanghai.jpg"},
    {"id": 10, "name": "Banana Cue",
     "description": "Deep-fried caramelized saba bananas on a stick.",
     "category": "Snacks", "price": 39.00, "image": "images/banana_cue.jpg"},
    {"id": 11, "name": "Cheesy Nachos",
     "description": "Tortilla chips with melted cheese and salsa.",
     "category": "Snacks", "price": 99.00, "image": "images/cheesy_nachos.jpg"},
    # ---------- drinks ----------
    {"id": 12, "name": "Iced Tea",
     "description": "Freshly brewed, lightly sweetened and chilled.",
     "category": "Drinks", "price": 45.00, "image": "images/iced_tea.jpg"},
    {"id": 13, "name": "Mango Shake",
     "description": "Thick and creamy shake made from ripe Davao mangoes.",
     "category": "Drinks", "price": 85.00, "image": "images/mango_shake.jpg"},
    {"id": 14, "name": "Calamansi Juice",
     "description": "Refreshing and tangy Philippine lime juice.",
     "category": "Drinks", "price": 55.00, "image": "images/calamansi_juice.jpg"},
    {"id": 15, "name": "Bottled Water",
     "description": "500 ml purified drinking water.",
     "category": "Drinks", "price": 25.00, "image": "images/bottled_water.jpg"},
]


def _load_menu():
    if os.path.exists(MENU_FILE):
        try:
            with open(MENU_FILE, "r", encoding="utf-8") as f:
                items = json.load(f)
            if isinstance(items, list):
                return items
        except (json.JSONDecodeError, OSError):
            pass
    return copy.deepcopy(_DEFAULT_ITEMS)


MENU_ITEMS = _load_menu()


def save_menu():
    tmp = MENU_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(MENU_ITEMS, f, indent=2, ensure_ascii=False)
    os.replace(tmp, MENU_FILE)


def resolve_image(path):
    if not path:
        return None
    full = path if os.path.isabs(path) else os.path.join(BASE_DIR, path)
    return full if os.path.exists(full) else None


def import_image(source_path):
    os.makedirs(IMAGES_DIR, exist_ok=True)
    base, ext = os.path.splitext(os.path.basename(source_path))
    name, n = base + ext.lower(), 1
    while os.path.exists(os.path.join(IMAGES_DIR, name)):
        if os.path.samefile(source_path, os.path.join(IMAGES_DIR, name)):
            break
        n += 1
        name = f"{base}_{n}{ext.lower()}"
    dest = os.path.join(IMAGES_DIR, name)
    if not (os.path.exists(dest) and os.path.samefile(source_path, dest)):
        shutil.copyfile(source_path, dest)
    return f"images/{name}"


def get_all_items():
    return MENU_ITEMS


def get_categories():
    return CATEGORIES
