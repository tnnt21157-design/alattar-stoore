from flask import Flask, render_template, request, redirect, url_for, session, flash
from urllib.parse import quote
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-key-before-publishing")

# عدّل الرقم إذا لزم الأمر. الصيغة الدولية للأردن بدون + أو أصفار البداية.
WHATSAPP_NUMBER = "962781611698"

CATEGORIES = {
    "herbs": {"title": "الأعشاب والزعتر", "description": "نكهات بلدية أصيلة من خيرات الطبيعة."},
    "grains": {"title": "البقوليات والحبوب", "description": "حبوب وبقوليات لاحتياجات مطبخك."},
    "spices": {"title": "البهارات والتوابل", "description": "تشكيلة من التوابل التي تضيف نكهة لأطباقك."},
    "pantry": {"title": "المونة البلدية", "description": "منتجات المونة البلدية حسب المتوفر في المحل."},
}

# الأسعار بالدينار الأردني حسب القائمة التي زوّدني بها المستخدم.
PRODUCTS = [
    {"id": "beans", "name": "فاصوليا", "price": 1.00, "category": "grains", "image": "beans.jpg", "description": "فاصوليا"},
    {"id": "lentils", "name": "عدس حب", "price": 1.00, "category": "grains", "image": "lentils.jpg", "description": "عدس حب"},
    {"id": "freekeh", "name": "فريكة جنين", "price": 2.50, "category": "grains", "image": "freekeh.jpg", "description": "فريكة جنين"},
    {"id": "mexican_chickpeas", "name": "حمص مكسيكي", "price": 1.50, "category": "grains", "image": "chickpeas.jpg", "description": "حمص مكسيكي"},
    {"id": "bulgur", "name": "برغل", "price": 0.75, "category": "grains", "image": "bulgur.jpg", "description": "برغل"},
    {"id": "local_fine_bulgur", "name": "برغل ناعم بلدي", "price": 1.00, "category": "grains", "image": "bulgur.jpg", "description": "برغل ناعم بلدي"},
    {"id": "local_wheat_flour", "name": "طحين قمح بلدي", "price": 1.00, "category": "pantry", "image": "wheat_flour.jpg", "description": "طحين قمح بلدي"},
    {"id": "local_wheat", "name": "قمح بلدي", "price": 0.75, "category": "grains", "image": "wheat.jpg", "description": "قمح بلدي"},
    {"id": "oats", "name": "شوفان", "price": 2.00, "category": "grains", "image": "oats.jpg", "description": "شوفان"},
    {"id": "starch", "name": "نشا سعودي", "price": 1.00, "category": "pantry", "image": "starch.jpg", "description": "نشا سعودي"},
    {"id": "baking_soda", "name": "كربونة", "price": 1.00, "category": "pantry", "image": "baking_soda.jpg", "description": "كربونة"},
    {"id": "local_zaatar", "name": "زعتر بلدي", "price": 2.50, "category": "herbs", "image": "zaatar.jpg", "description": "زعتر بلدي"},
    {"id": "zaatar_leaves", "name": "زعتر ورق", "price": 4.00, "category": "herbs", "image": "zaatar_leaves.jpg", "description": "زعتر ورق"},
    {"id": "cinnamon_sticks", "name": "قرفة خشب", "price": 3.50, "category": "spices", "image": "cinnamon.jpg", "description": "قرفة خشب"},
    {"id": "cinnamon_cigar", "name": "قرفة سيجار", "price": 6.00, "category": "spices", "image": "cinnamon.jpg", "description": "قرفة سيجار"},
    {"id": "extra_coffee", "name": "قهوة إكسترا", "price": 6.00, "category": "pantry", "image": "coffee.jpg", "description": "قهوة إكسترا"},
    {"id": "matcha", "name": "شاي ماتشا", "price": 2.00, "category": "herbs", "image": "matcha.jpg", "description": "شاي ماتشا"},
]

PRODUCT_BY_ID = {p["id"]: p for p in PRODUCTS}

def cart_items():
    cart = session.get("cart", {})
    items = []
    total = 0
    for product_id, quantity in cart.items():
        product = PRODUCT_BY_ID.get(product_id)
        if product and isinstance(quantity, int) and quantity > 0:
            item_total = product["price"] * quantity
            items.append({**product, "quantity": quantity, "subtotal": item_total})
            total += item_total
    return items, round(total, 2)

@app.context_processor
def shared_template_data():
    items, total = cart_items()
    return {"categories": CATEGORIES, "cart_count": sum(i["quantity"] for i in items)}

@app.route("/")
def home():
    featured = [PRODUCT_BY_ID[i] for i in ["local_zaatar", "freekeh", "cinnamon_sticks", "lentils"]]
    return render_template("index.html", featured=featured)

@app.route("/category/<category_id>")
def category(category_id):
    if category_id not in CATEGORIES:
        return redirect(url_for("home"))
    products = [p for p in PRODUCTS if p["category"] == category_id]
    return render_template("category.html", category=CATEGORIES[category_id], category_id=category_id, products=products)

@app.route("/cart")
def cart():
    items, total = cart_items()
    return render_template("cart.html", items=items, total=total)

@app.post("/cart/add/<product_id>")
def add_to_cart(product_id):
    if product_id not in PRODUCT_BY_ID:
        flash("هذا المنتج غير موجود.", "error")
        return redirect(url_for("home"))
    try:
        quantity = int(request.form.get("quantity", "1"))
    except ValueError:
        quantity = 1
    quantity = max(1, min(quantity, 50))
    cart = session.get("cart", {})
    cart[product_id] = min(50, int(cart.get(product_id, 0)) + quantity)
    session["cart"] = cart
    flash(f"أُضيف {PRODUCT_BY_ID[product_id]['name']} إلى السلة.", "success")
    return redirect(request.referrer or url_for("home"))

@app.post("/cart/update")
def update_cart():
    cart = session.get("cart", {})
    updated = {}
    for product_id in list(cart.keys()):
        try:
            quantity = int(request.form.get(product_id, cart[product_id]))
        except (ValueError, TypeError):
            quantity = 0
        if product_id in PRODUCT_BY_ID and quantity > 0:
            updated[product_id] = min(50, quantity)
    session["cart"] = updated
    flash("تم تحديث السلة.", "success")
    return redirect(url_for("cart"))

@app.post("/cart/remove/<product_id>")
def remove_from_cart(product_id):
    cart = session.get("cart", {})
    cart.pop(product_id, None)
    session["cart"] = cart
    return redirect(url_for("cart"))

@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    items, total = cart_items()
    if not items:
        flash("سلة المشتريات فارغة.", "error")
        return redirect(url_for("cart"))
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        phone = request.form.get("phone", "").strip()
        area = request.form.get("area", "").strip()
        address = request.form.get("address", "").strip()
        notes = request.form.get("notes", "").strip()
        if not name or not phone or not area:
            flash("يرجى تعبئة الاسم ورقم الهاتف والمنطقة.", "error")
            return render_template("checkout.html", items=items, total=total)
        lines = [
            "طلب جديد من متجر العطّار 🌿",
            f"الاسم: {name}",
            f"رقم الهاتف: {phone}",
            f"منطقة التوصيل: {area}",
        ]
        if address:
            lines.append(f"العنوان: {address}")
        lines += ["", "المنتجات:"]
        for item in items:
            lines.append(f"{item['name']} × {item['quantity']} = {item['subtotal']:.2f} د.أ")
        lines.append("")
        lines.append(f"الإجمالي قبل التوصيل: {total:.2f} د.أ")
        lines.append("أجرة التوصيل تبدأ من 1 دينار حسب المنطقة.")
        if notes:
            lines.append(f"ملاحظات: {notes}")
        message = quote("\n".join(lines))
        return redirect(f"https://wa.me/{WHATSAPP_NUMBER}?text={message}")
    return render_template("checkout.html", items=items, total=total)

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/contact")
def contact():
    return render_template("contact.html", whatsapp=WHATSAPP_NUMBER)

if __name__ == "__main__":
    if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))