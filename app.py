import os
import re
import sqlite3
from functools import wraps
from urllib.parse import quote

from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, abort
)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-before-deploy")
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

WHATSAPP_NUMBER = "962781611698"
DATABASE = os.environ.get("DATABASE_PATH") or (
    "/var/data/alattar.db" if os.environ.get("RENDER") else "alattar.db"
)

CATEGORIES = {
    "herbs": "الأعشاب الطبيعية",
    "grains": "البقوليات والحبوب",
    "spices": "البهارات والتوابل",
    "mixes": "خلطات البهارات",
    "pantry": "المونة البلدية",
    "men_perfumes": "العطور الرجالية",
    "women_perfumes": "العطور النسائية",
    "oil_perfumes": "العطور الزيتية",
    "musk": "المسك",
    "oud": "العود",
    "hair_oils": "زيوت الشعر",
    "skin_oils": "زيوت البشرة",
    "natural_oils": "الزيوت الطبيعية",
    "nuts": "المكسرات والتسالي",
    "care": "منتجات العناية",
    "offers": "العروض والخصومات",
}

OLD_PRODUCTS = [
    ("beans", "فاصوليا", 1.00, "grains", "beans.jpg"),
    ("lentils", "عدس حب", 1.00, "grains", "lentils.jpg"),
    ("freekeh", "فريكة جنين", 2.50, "grains", "freekeh.jpg"),
    ("mexican_chickpeas", "حمص مكسيكي", 1.50, "grains", "chickpeas.jpg"),
    ("bulgur", "برغل", 0.75, "grains", "bulgur.jpg"),
    ("local_fine_bulgur", "برغل ناعم بلدي", 1.00, "grains", "bulgur.jpg"),
    ("local_wheat_flour", "طحين قمح بلدي", 1.00, "pantry", "wheat_flour.jpg"),
    ("local_wheat", "قمح بلدي", 0.75, "grains", "wheat.jpg"),
    ("oats", "شوفان", 2.00, "grains", "oats.jpg"),
    ("starch", "نشا سعودي", 1.00, "pantry", "starch.jpg"),
    ("baking_soda", "كربونة", 1.00, "pantry", "baking_soda.jpg"),
    ("local_zaatar", "زعتر بلدي", 2.50, "herbs", "zaatar.jpg"),
    ("zaatar_leaves", "زعتر ورق", 4.00, "herbs", "zaatar_leaves.jpg"),
    ("cinnamon_sticks", "قرفة خشب", 3.50, "spices", "cinnamon.jpg"),
    ("cinnamon_cigar", "قرفة سيجار", 6.00, "spices", "cinnamon.jpg"),
    ("extra_coffee", "قهوة إكسترا", 6.00, "pantry", "coffee.jpg"),
    ("matcha", "شاي ماتشا", 2.00, "herbs", "matcha.jpg"),
]

HERBS = [
    "بابونج", "يانسون", "ميرمية", "زهورات", "زعتر بري",
    "إكليل الجبل", "زعتر أخضر", "نعناع مجفف", "كركديه",
    "لويزة", "خزامى", "شمر", "حلبة", "قراص", "ملّيسة"
]

SPICES = [
    "فلفل أسود", "فلفل أبيض", "فلفل أحمر", "كركم",
    "كمون", "كزبرة", "قرفة", "هيل", "زنجبيل", "قرنفل",
    "جوزة الطيب", "سماق", "بابريكا", "كاري", "زعفران",
    "يانسون نجمي", "حبة البركة", "خردل", "ثوم بودرة",
    "بصل بودرة", "فلفل حار", "ليمون مجفف", "ورق غار",
    "محلب", "مستكة", "حبهان مطحون"
]

MIXES = [
    "بهارات مشكلة", "بهارات منسف", "بهارات كبسة",
    "بهارات شاورما", "بهارات دجاج", "بهارات لحمة",
    "بهارات سمك", "بهارات مشاوي", "بهارات فلافل",
    "بهارات مقلوبة", "بهارات مندي", "بهارات برياني",
    "بهارات بطاطا", "بهارات بيتزا"
]

GRAINS = [
    "عدس أحمر", "عدس أسود", "فاصوليا بيضاء", "فاصوليا حمراء",
    "حمص", "فول", "فريكة", "برغل خشن", "برغل ناعم",
    "قمح", "أرز بسمتي", "أرز مصري", "شوفان", "ذرة",
    "بازيلاء مجففة", "لوبيا"
]

PANTRY = [
    "زعتر بلدي", "زيت زيتون", "سماق", "مكدوس",
    "دبس رمان", "مخللات", "دبس تمر", "طحينة",
    "دبس عنب", "مربى بلدي"
]

OILS = [
    "زيت سمسم", "زيت خروع", "زيت زيتون", "زيت جوز الهند",
    "زيت اللوز الحلو", "زيت اللوز المر", "زيت الأرغان",
    "زيت الحبة السوداء", "زيت الجوجوبا", "زيت الجرجير",
    "زيت إكليل الجبل", "زيت النعناع", "زيت القرنفل",
    "زيت بذور العنب", "زيت الأفوكادو", "زيت دوار الشمس",
    "زيت الكتان", "زيت الخردل", "زيت شجرة الشاي",
    "زيت اللافندر", "زيت الكافور", "زيت الثوم",
    "زيت الصبار", "زيت جنين القمح", "زيت الورد"
]

NUTS = [
    "لوز", "كاجو", "فستق", "جوز", "بندق",
    "زبيب", "فول سوداني", "بذور دوار الشمس",
    "بذور القرع", "لب أبيض", "لب أسود"
]

MEN_PERFUMES = [
    "عطر رجالي فاخر", "عطر رجالي خشبي", "عطر رجالي شرقي",
    "عطر رجالي منعش", "عطر رجالي حمضي", "عطر رجالي بحري",
    "عطر رجالي جلدي", "عطر رجالي عنبري", "عطر رجالي مسكي",
    "عطر رجالي فواح", "عطر رجالي يومي", "عطر رجالي للمناسبات",
    "عطر رجالي كلاسيكي", "عطر رجالي عصري", "عطر رجالي حار",
    "عطر رجالي بارد", "عطر رجالي صيفي", "عطر رجالي شتوي",
    "عطر رجالي رياضي", "عطر رجالي رسمي"
]

WOMEN_PERFUMES = [
    "عطر نسائي زهري", "عطر نسائي فواكه", "عطر نسائي شرقي",
    "عطر نسائي فانيلا", "عطر نسائي مسكي", "عطر نسائي عنبري",
    "عطر نسائي ناعم", "عطر نسائي فاخر", "عطر نسائي منعش",
    "عطر نسائي حلو", "عطر نسائي بودري", "عطر نسائي خشبي",
    "عطر نسائي حمضي", "عطر نسائي كلاسيكي", "عطر نسائي عصري"
]

OIL_PERFUMES = [
    "عطر زيتي ورد", "عطر زيتي مسك", "عطر زيتي عود",
    "عطر زيتي فانيلا", "عطر زيتي عنبر", "عطر زيتي ياسمين",
    "عطر زيتي زعفران", "عطر زيتي صندل", "عطر زيتي زهري",
    "عطر زيتي شرقي"
]

MUSK = [
    "مسك أبيض", "مسك أسود", "مسك طهارة", "مسك ورد",
    "مسك فانيلا", "مسك عنبر", "مسك بودري", "مسك سائل",
    "مسك جامد", "مسك مركز"
]

OUD = [
    "عود كمبودي", "عود هندي", "عود ماليزي", "عود لاوسي",
    "عود بخور", "دهن عود", "عود مروكي", "عود طبيعي",
    "عود فاخر", "عود معطر"
]

def db():
    con = sqlite3.connect(DATABASE)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    with db() as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                price REAL,
                category TEXT NOT NULL,
                image TEXT DEFAULT '',
                description TEXT DEFAULT '',
                old_price REAL,
                active INTEGER DEFAULT 1
            )
        """)

        for key, title in CATEGORIES.items():
            con.execute("""
                CREATE TABLE IF NOT EXISTS categories (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    active INTEGER DEFAULT 1
                )
            """)
            con.execute(
                "INSERT OR IGNORE INTO categories(id,title) VALUES(?,?)",
                (key, title)
            )

        for pid, name, price, category, image in OLD_PRODUCTS:
            con.execute("""
                INSERT OR IGNORE INTO products
                (id,name,price,category,image,description)
                VALUES(?,?,?,?,?,?)
            """, (pid, name, price, category, image, name))

        groups = {
            "herbs": HERBS,
            "spices": SPICES,
            "mixes": MIXES,
            "grains": GRAINS,
            "pantry": PANTRY,
            "hair_oils": OILS,
            "skin_oils": OILS,
            "natural_oils": OILS,
            "nuts": NUTS,
            "men_perfumes": MEN_PERFUMES,
            "women_perfumes": WOMEN_PERFUMES,
            "oil_perfumes": OIL_PERFUMES,
            "musk": MUSK,
            "oud": OUD,
        }

        for category, names in groups.items():
            for index, name in enumerate(names, 1):
                pid = f"{category}_{index}"
                con.execute("""
                    INSERT OR IGNORE INTO products
                    (id,name,price,category,image,description)
                    VALUES(?,?,NULL,?,'',?)
                """, (pid, name, category, name))

        # إكمال 100 اسم عطر موزعة على الأقسام الخمسة
        perfume_groups = {
            "men_perfumes": MEN_PERFUMES,
            "women_perfumes": WOMEN_PERFUMES,
            "oil_perfumes": OIL_PERFUMES,
            "musk": MUSK,
            "oud": OUD,
        }
        perfume_number = 1
        for category, names in perfume_groups.items():
            for name in names:
                if perfume_number > 100:
                    break
                perfume_number += 1

        con.commit()

init_db()

def get_categories():
    with db() as con:
        rows = con.execute(
            "SELECT * FROM categories WHERE active=1 ORDER BY rowid"
        ).fetchall()
    return {r["id"]: {"title": r["title"]} for r in rows}

def get_products(category=None, active_only=True):
    with db() as con:
        sql = "SELECT * FROM products"
        conditions = []
        params = []
        if category:
            conditions.append("category=?")
            params.append(category)
        if active_only:
            conditions.append("active=1")
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        sql += " ORDER BY rowid"
        rows = con.execute(sql, params).fetchall()
    return [dict(r) for r in rows]

def get_product(product_id):
    with db() as con:
        row = con.execute(
            "SELECT * FROM products WHERE id=?", (product_id,)
        ).fetchone()
    return dict(row) if row else None

def current_price(product):
    price = product["price"]
    if price is None:
        return None
    return float(price)

def cart_items():
    cart_data = session.get("cart", {})
    items = []
    total = 0

    for pid, quantity in cart_data.items():
        product = get_product(pid)
        if not product or not product["active"]:
            continue
        try:
            quantity = max(1, min(50, int(quantity)))
        except (ValueError, TypeError):
            continue

        price = current_price(product)
        if price is None:
            continue

        old_price = product["old_price"]
        if old_price is not None and float(old_price) > price:
            pass

        subtotal = round(price * quantity, 2)
        items.append({
            **product,
            "price": price,
            "quantity": quantity,
            "subtotal": subtotal
        })
        total += subtotal

    return items, round(total, 2)

@app.context_processor
def shared_data():
    items, total = cart_items()
    return {
        "categories": get_categories(),
        "cart_count": sum(i["quantity"] for i in items)
    }

@app.route("/")
def home():
    featured_ids = [
        "local_zaatar", "freekeh",
        "cinnamon_sticks", "lentils"
    ]
    featured = [
        get_product(pid) for pid in featured_ids
        if get_product(pid)
    ]
    return render_template("index.html", featured=featured)

@app.route("/category/<category_id>")
def category(category_id):
    categories = get_categories()
    if category_id not in categories:
        return redirect(url_for("home"))
    return render_template(
        "category.html",
        category=categories[category_id],
        category_id=category_id,
        products=get_products(category_id)
    )

@app.route("/cart")
def cart():
    items, total = cart_items()
    return render_template("cart.html", items=items, total=total)

@app.post("/cart/add/<product_id>")
def add_to_cart(product_id):
    product = get_product(product_id)
    if not product or not product["active"] or product["price"] is None:
        flash("المنتج غير متوفر للبيع حالياً.", "error")
        return redirect(request.referrer or url_for("home"))

    try:
        quantity = int(request.form.get("quantity", "1"))
    except ValueError:
        quantity = 1

    quantity = max(1, min(quantity, 50))
    cart_data = session.get("cart", {})
    cart_data[product_id] = min(
        50, int(cart_data.get(product_id, 0)) + quantity
    )
    session["cart"] = cart_data
    flash(f"تمت إضافة {product['name']} إلى السلة.", "success")
    return redirect(request.referrer or url_for("home"))

@app.post("/cart/update")
def update_cart():
    cart_data = session.get("cart", {})
    updated = {}
    for pid in cart_data:
        try:
            quantity = int(request.form.get(pid, cart_data[pid]))
        except (ValueError, TypeError):
            quantity = 0
        if get_product(pid) and quantity > 0:
            updated[pid] = min(50, quantity)
    session["cart"] = updated
    flash("تم تحديث السلة.", "success")
    return redirect(url_for("cart"))

@app.post("/cart/remove/<product_id>")
def remove_from_cart(product_id):
    cart_data = session.get("cart", {})
    cart_data.pop(product_id, None)
    session["cart"] = cart_data
    return redirect(url_for("cart"))

@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    items, total = cart_items()
    if not items:
        flash("سلة المشتريات فارغة أو لم يتم تحديد أسعار المنتجات.", "error")
        return redirect(url_for("cart"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        phone = request.form.get("phone", "").strip()
        area = request.form.get("area", "").strip()
        address = request.form.get("address", "").strip()
        notes = request.form.get("notes", "").strip()

        if not name or not phone or not area:
            flash("يرجى تعبئة الاسم ورقم الهاتف والمنطقة.", "error")
            return render_template(
                "checkout.html", items=items, total=total
            )

        lines = [
            "طلب جديد من متجر العطّار 🌿",
            f"الاسم: {name}",
            f"رقم الهاتف: {phone}",
            f"منطقة التوصيل: {area}",
            "",
            "المنتجات:"
        ]

        for item in items:
            lines.append(
                f"{item['name']} × {item['quantity']} = "
                f"{item['subtotal']:.2f} د.أ"
            )

        lines += [
            "",
            f"الإجمالي قبل التوصيل: {total:.2f} د.أ",
            "التوصيل يبدأ من 1 دينار حسب المنطقة."
        ]
        if address:
            lines.append(f"العنوان: {address}")
        if notes:
            lines.append(f"ملاحظات: {notes}")

        return redirect(
            f"https://wa.me/{WHATSAPP_NUMBER}?text={quote(chr(10).join(lines))}"
        )

    return render_template("checkout.html", items=items, total=total)

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/contact")
def contact():
    return render_template("contact.html", whatsapp=WHATSAPP_NUMBER)

# ---------------- ADMIN ----------------

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin_login"))
        return fn(*args, **kwargs)
    return wrapper

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        password = request.form.get("password", "")
        expected = os.environ.get("ADMIN_PASSWORD")
        if not expected:
            abort(503, "ADMIN_PASSWORD is not configured")
        if password and password == expected:
            session["admin_logged_in"] = True
            return redirect(url_for("admin"))
        flash("كلمة المرور غير صحيحة.", "error")
    return render_template("admin_login.html")

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    return redirect(url_for("home"))

@app.route("/admin")
@admin_required
def admin():
    products = get_products(active_only=False)
    return render_template(
        "admin.html",
        products=products,
        categories=get_categories()
    )

@app.route("/admin/product/save", methods=["POST"])
@admin_required
def admin_save_product():
    pid = request.form.get("id", "").strip()
    name = request.form.get("name", "").strip()
    category = request.form.get("category", "").strip()
    price_text = request.form.get("price", "").strip()
    old_price_text = request.form.get("old_price", "").strip()
    image = request.form.get("image", "").strip()
    description = request.form.get("description", "").strip()

    if not name or category not in get_categories():
        flash("أدخل اسم المنتج واختر قسماً صحيحاً.", "error")
        return redirect(url_for("admin"))

    if not pid:
        pid = re.sub(r"[^a-zA-Z0-9_-]", "_", name)[:35]
        pid = pid or "product"
        import uuid
        pid = f"{pid}_{uuid.uuid4().hex[:6]}"

    try:
        price = float(price_text) if price_text else None
        old_price = float(old_price_text) if old_price_text else None
        if price is not None and price < 0:
            raise ValueError
        if old_price is not None and old_price < 0:
            raise ValueError
    except ValueError:
        flash("السعر غير صحيح.", "error")
        return redirect(url_for("admin"))

    with db() as con:
        con.execute("""
            INSERT INTO products
            (id,name,price,category,image,description,old_price)
            VALUES(?,?,?,?,?,?,?)
            ON CONFLICT(id) DO UPDATE SET
            name=excluded.name,
            price=excluded.price,
            category=excluded.category,
            image=excluded.image,
            description=excluded.description,
            old_price=excluded.old_price
        """, (
            pid, name, price, category, image,
            description, old_price
        ))
        con.commit()

    flash("تم حفظ المنتج.", "success")
    return redirect(url_for("admin"))

@app.post("/admin/product/delete/<product_id>")
@admin_required
def admin_delete_product(product_id):
    with db() as con:
        con.execute(
            "DELETE FROM products WHERE id=?", (product_id,)
        )
        con.commit()
    flash("تم حذف المنتج.", "success")
    return redirect(url_for("admin"))

@app.post("/admin/product/toggle/<product_id>")
@admin_required
def admin_toggle_product(product_id):
    with db() as con:
        con.execute("""
            UPDATE products SET active =
            CASE WHEN active=1 THEN 0 ELSE 1 END
            WHERE id=?
        """, (product_id,))
        con.commit()
    return redirect(url_for("admin"))

@app.post("/admin/category/save")
@admin_required
def admin_save_category():
    cid = request.form.get("id", "").strip()
    title = request.form.get("title", "").strip()
    if not cid or not title:
        flash("أدخل اسم القسم ورمزه.", "error")
        return redirect(url_for("admin"))
    with db() as con:
        con.execute("""
            INSERT INTO categories(id,title)
            VALUES(?,?)
            ON CONFLICT(id) DO UPDATE SET title=excluded.title
        """, (cid, title))
        con.commit()
    return redirect(url_for("admin"))

@app.post("/admin/category/toggle/<category_id>")
@admin_required
def admin_toggle_category(category_id):
    with db() as con:
        con.execute("""
            UPDATE categories SET active =
            CASE WHEN active=1 THEN 0 ELSE 1 END
            WHERE id=?
        """, (category_id,))
        con.commit()
    return redirect(url_for("admin"))

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False
    )