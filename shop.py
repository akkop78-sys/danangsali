from __future__ import annotations

from functools import wraps

from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from admin_routes import admin_bp
from config import Config
from models import CATEGORIES, Order, OrderItem, Product, User, db
from payments import create_payment
from reviews import FEATURED_REVIEWS, QUICK_QUOTES
from seed import seed_database


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)
    Config.UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    app.register_blueprint(admin_bp)

    app.jinja_env.filters["krw"] = lambda value: f"{int(value):,}원"

    @app.context_processor
    def inject_globals():
        user = None
        if session.get("user_id"):
            user = User.query.get(session["user_id"])
        return {
            "shop_name": app.config["SHOP_NAME"],
            "cart_count": cart_count(),
            "categories": CATEGORIES,
            "current_user": user,
            "payment_mode": app.config.get("PAYMENT_MODE", "demo"),
        }

    def login_required(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not session.get("user_id"):
                flash("로그인이 필요해요.", "error")
                return redirect(url_for("login", next=request.path))
            return view(*args, **kwargs)

        return wrapped

    def get_cart() -> list[dict]:
        return session.setdefault("cart", [])

    def cart_count() -> int:
        return sum(item["qty"] for item in get_cart())

    def cart_total() -> int:
        total = 0
        for item in get_cart():
            product = Product.query.get(item["product_id"])
            if product:
                total += product.price * item["qty"]
        return total

    def product_image_url(product: Product) -> str:
        if product.image_path:
            return url_for("static", filename=product.image_path)
        return product.image_url or ""

    app.jinja_env.globals["product_image"] = product_image_url

    @app.route("/")
    def index():
        category = request.args.get("category", "전체")
        query = Product.query.filter_by(is_active=True)
        if category != "전체":
            query = query.filter_by(category=category)
        products = query.order_by(Product.id.desc()).all()
        return render_template(
            "index.html",
            products=products,
            active_category=category,
            featured_reviews=FEATURED_REVIEWS,
            quick_quotes=QUICK_QUOTES,
        )

    @app.route("/product/<slug>")
    def product_detail(slug: str):
        product = Product.query.filter_by(slug=slug, is_active=True).first()
        if not product:
            flash("상품을 찾을 수 없어요.", "error")
            return redirect(url_for("index"))
        related = (
            Product.query.filter(
                Product.category == product.category,
                Product.id != product.id,
                Product.is_active.is_(True),
            )
            .limit(3)
            .all()
        )
        return render_template("product.html", product=product, related=related)

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            if not name or not email or not password:
                flash("모든 항목을 입력해 주세요.", "error")
            elif len(password) < 6:
                flash("비밀번호는 6자 이상으로 해 주세요.", "error")
            elif User.query.filter_by(email=email).first():
                flash("이미 가입된 이메일이에요.", "error")
            else:
                user = User(email=email, name=name, is_admin=False)
                user.set_password(password)
                db.session.add(user)
                db.session.commit()
                session["user_id"] = user.id
                session["is_admin"] = False
                flash(f"{name}님, 가입을 환영해요!", "success")
                return redirect(url_for("index"))
        return render_template("auth/register.html")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            user = User.query.filter_by(email=email).first()
            if user and user.check_password(password):
                session["user_id"] = user.id
                session["is_admin"] = bool(user.is_admin)
                flash(f"{user.name}님, 반가워요!", "success")
                next_url = request.args.get("next") or url_for("index")
                return redirect(next_url)
            flash("이메일 또는 비밀번호가 올바르지 않아요.", "error")
        return render_template("auth/login.html")

    @app.route("/logout")
    def logout():
        session.pop("user_id", None)
        session.pop("is_admin", None)
        flash("로그아웃했어요.", "success")
        return redirect(url_for("index"))

    @app.route("/cart")
    def cart():
        items = []
        for item in get_cart():
            product = Product.query.get(item["product_id"])
            if not product:
                continue
            items.append(
                {
                    **item,
                    "product": product,
                    "line_total": product.price * item["qty"],
                }
            )
        return render_template("cart.html", items=items, total=cart_total())

    @app.route("/cart/add", methods=["POST"])
    def cart_add():
        product_id = int(request.form.get("product_id") or 0)
        size = request.form.get("size", "FREE")
        qty = max(1, min(10, int(request.form.get("qty", 1))))

        product = Product.query.get(product_id)
        if not product or not product.is_active:
            flash("상품을 찾을 수 없어요.", "error")
            return redirect(url_for("index"))

        if size not in product.size_list():
            flash("선택하신 사이즈가 없어요.", "error")
            return redirect(url_for("product_detail", slug=product.slug))

        if product.stock < qty:
            flash(f"재고가 부족해요. (남은 수량: {product.stock})", "error")
            return redirect(url_for("product_detail", slug=product.slug))

        cart = get_cart()
        for item in cart:
            if item["product_id"] == product_id and item["size"] == size:
                item["qty"] = min(10, item["qty"] + qty)
                break
        else:
            cart.append({"product_id": product_id, "size": size, "qty": qty})

        session["cart"] = cart
        session.modified = True
        flash(f"{product.name}을(를) 장바구니에 담았어요.", "success")
        return redirect(url_for("cart"))

    @app.route("/cart/update", methods=["POST"])
    def cart_update():
        product_id = int(request.form.get("product_id") or 0)
        size = request.form.get("size", "")
        action = request.form.get("action", "")

        cart = get_cart()
        new_cart = []
        for item in cart:
            if item["product_id"] == product_id and item["size"] == size:
                if action == "inc":
                    item["qty"] = min(10, item["qty"] + 1)
                    new_cart.append(item)
                elif action == "dec":
                    if item["qty"] > 1:
                        item["qty"] -= 1
                        new_cart.append(item)
                elif action == "remove":
                    continue
                else:
                    new_cart.append(item)
            else:
                new_cart.append(item)

        session["cart"] = new_cart
        session.modified = True
        return redirect(url_for("cart"))

    @app.route("/checkout", methods=["GET", "POST"])
    @login_required
    def checkout():
        cart = get_cart()
        if not cart:
            flash("장바구니가 비어 있어요.", "error")
            return redirect(url_for("index"))

        user = User.query.get(session["user_id"])

        if request.method == "POST":
            name = request.form.get("name", "").strip()
            phone = request.form.get("phone", "").strip()
            address = request.form.get("address", "").strip()
            if not name or not phone or not address:
                flash("배송 정보를 모두 입력해 주세요.", "error")
                return redirect(url_for("checkout"))

            # 재고 확인
            for item in cart:
                product = Product.query.get(item["product_id"])
                if not product or product.stock < item["qty"]:
                    flash(
                        f"{(product.name if product else '상품')} 재고가 부족해요.",
                        "error",
                    )
                    return redirect(url_for("cart"))

            total = cart_total()
            payment = create_payment(
                amount=total,
                order_id=f"demo-{user.id}-{total}",
                order_name=f"{app.config['SHOP_NAME']} 주문",
                customer_name=name,
                client_key=app.config.get("TOSS_CLIENT_KEY", ""),
                payment_mode=app.config.get("PAYMENT_MODE", "demo"),
            )
            if not payment.ok:
                flash(payment.message, "error")
                return redirect(url_for("checkout"))

            order = Order(
                user_id=user.id,
                buyer_name=name,
                buyer_phone=phone,
                buyer_address=address,
                total=total,
                status="접수",
                payment_mode=payment.mode,
            )
            db.session.add(order)
            db.session.flush()

            for item in cart:
                product = Product.query.get(item["product_id"])
                db.session.add(
                    OrderItem(
                        order_id=order.id,
                        product_id=product.id,
                        product_name=product.name,
                        size=item["size"],
                        qty=item["qty"],
                        unit_price=product.price,
                    )
                )
                product.stock -= item["qty"]

            db.session.commit()
            session.pop("cart", None)
            flash(payment.message, "success")
            return render_template("order_done.html", order=order)

        items = []
        for item in cart:
            product = Product.query.get(item["product_id"])
            if product:
                items.append({**item, "product": product})
        return render_template(
            "checkout.html",
            items=items,
            total=cart_total(),
            user=user,
        )

    @app.route("/orders")
    @login_required
    def my_orders():
        orders = (
            Order.query.filter_by(user_id=session["user_id"])
            .order_by(Order.created_at.desc())
            .all()
        )
        return render_template("orders.html", orders=orders)

    with app.app_context():
        db.create_all()
        seed_database(
            admin_username=app.config["ADMIN_USERNAME"],
            admin_password=app.config["ADMIN_PASSWORD"],
        )

    return app


app = create_app()


if __name__ == "__main__":
    import os

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=os.environ.get("FLASK_DEBUG") == "1")
