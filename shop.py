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
from guides import GUIDES, get_guide
from models import CATEGORIES, Inquiry, Order, OrderItem, Product, User, db
from notify import notify_new_inquiry, notify_new_order
from payments import create_payment
from reviews import FEATURED_REVIEWS, QUICK_QUOTES
from seed import seed_database


def _sms_href(phone: str) -> str:
    """화면에 번호 노출 없이 문자 앱만 열 링크. (번호는 HTML 속성에만 사용)"""
    digits = "".join(ch for ch in (phone or "") if ch.isdigit())
    if not digits:
        return ""
    # 한국 휴대폰 010… → 국제형 +82
    if digits.startswith("0"):
        digits = "82" + digits[1:]
    body = "다낭살이 문의드립니다."
    from urllib.parse import quote

    return f"sms:+{digits}?&body={quote(body)}"


def _mailto_href(email: str) -> str:
    """화면에 주소 노출 없이 메일 앱만 열 링크."""
    addr = (email or "").strip()
    if "@" not in addr:
        return ""
    from urllib.parse import quote

    subject = quote("다낭살이 문의")
    body = quote("다낭살이 문의드립니다.\n\n주문번호:\n내용:\n")
    return f"mailto:{addr}?subject={subject}&body={body}"


def _public_kakao(kakao: str) -> str:
    """이메일을 카톡 ID로 쓴 경우 화면에 노출하지 않음."""
    value = (kakao or "").strip()
    if not value or "@" in value:
        return ""
    return value


def _ensure_product_columns() -> None:
    """Add newly introduced columns on existing SQLite DBs."""
    try:
        rows = db.session.execute(db.text("PRAGMA table_info(products)")).fetchall()
    except Exception:
        return
    cols = {row[1] for row in rows}
    if "detail_html" not in cols:
        db.session.execute(
            db.text("ALTER TABLE products ADD COLUMN detail_html TEXT DEFAULT ''")
        )
        db.session.commit()


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
            # 문자·메일은 중간 경로로만 연결해 페이지에 주소/번호를 남기지 않음
            "shop_sms_enabled": bool(_sms_href(app.config.get("SHOP_PHONE", ""))),
            "shop_mail_enabled": bool(_mailto_href(app.config.get("SHOP_EMAIL", ""))),
            # 카톡 ID가 이메일이면 화면에 그대로 찍지 않음
            "shop_kakao_public": _public_kakao(app.config.get("SHOP_KAKAO", "")),
            "shop_hours": app.config.get("SHOP_HOURS", ""),
            "bank_name": app.config.get("SHOP_BANK_NAME", ""),
            "bank_account": app.config.get("SHOP_BANK_ACCOUNT", ""),
            "bank_holder": app.config.get("SHOP_BANK_HOLDER", ""),
            "bank_note": app.config.get("SHOP_BANK_NOTE", ""),
            "bank_ready": bool(
                app.config.get("SHOP_BANK_NAME")
                and app.config.get("SHOP_BANK_ACCOUNT")
                and app.config.get("SHOP_BANK_HOLDER")
            ),
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
            guides=GUIDES,
        )

    @app.route("/guides")
    def guides_index():
        return render_template("guides/index.html", guides=GUIDES)

    @app.route("/guides/<slug>")
    def guide_detail(slug: str):
        guide = get_guide(slug)
        if not guide:
            flash("가이드를 찾을 수 없어요.", "error")
            return redirect(url_for("guides_index"))
        related = [g for g in GUIDES if g["slug"] != slug][:3]
        return render_template("guides/detail.html", guide=guide, related=related)

    @app.route("/robots.txt")
    def robots_txt():
        body = (
            "User-agent: *\n"
            "Allow: /\n"
            f"Sitemap: {request.url_root.rstrip('/')}/sitemap.xml\n"
        )
        return app.response_class(body, mimetype="text/plain")

    @app.route("/sitemap.xml")
    def sitemap_xml():
        base = request.url_root.rstrip("/")
        urls = [
            "/",
            "/guides",
            "/contact",
            "/guides/danang-panty-guide",
            "/guides/jewel-vs-jiller",
            "/guides/underwear-buy-tips",
        ]
        for product in Product.query.filter_by(is_active=True).all():
            urls.append(f"/product/{product.slug}")
        items = "\n".join(
            f"  <url><loc>{base}{path}</loc><changefreq>weekly</changefreq></url>"
            for path in urls
        )
        xml = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            f"{items}\n"
            "</urlset>\n"
        )
        return app.response_class(xml, mimetype="application/xml")

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
                flash(
                    "이미 가입된 이메일이에요. 로그인하시거나, 비회원으로 바로 주문하세요.",
                    "error",
                )
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
    def checkout():
        """회원 가입 없이 주문 가능 (무통장 입금)."""
        cart = get_cart()
        if not cart:
            flash("장바구니가 비어 있어요.", "error")
            return redirect(url_for("index"))

        user = None
        if session.get("user_id"):
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
            order_key = f"bank-{(user.id if user else 'guest')}-{total}"
            payment = create_payment(
                amount=total,
                order_id=order_key,
                order_name=f"{app.config['SHOP_NAME']} 주문",
                customer_name=name,
                client_key=app.config.get("TOSS_CLIENT_KEY", ""),
                payment_mode=app.config.get("PAYMENT_MODE", "bank"),
            )
            if not payment.ok:
                flash(payment.message, "error")
                return redirect(url_for("checkout"))

            order = Order(
                user_id=user.id if user else None,
                buyer_name=name,
                buyer_phone=phone,
                buyer_address=address,
                total=total,
                status="입금대기" if payment.mode == "bank" else "접수",
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
            notify_new_order(order)
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

    @app.route("/contact", methods=["GET", "POST"])
    def contact():
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            phone = request.form.get("phone", "").strip()
            email = request.form.get("email", "").strip()
            order_ref = request.form.get("order_ref", "").strip()
            message = request.form.get("message", "").strip()
            if not name or not message:
                flash("이름과 문의 내용을 입력해 주세요.", "error")
            elif not phone and not email:
                flash("전화 또는 이메일 중 하나는 남겨 주세요.", "error")
            else:
                inquiry = Inquiry(
                    name=name,
                    phone=phone,
                    email=email,
                    order_ref=order_ref,
                    message=message,
                )
                db.session.add(inquiry)
                db.session.commit()
                notify_new_inquiry(inquiry)
                flash(
                    "문의가 접수됐어요. 확인 후 연락드릴게요.",
                    "success",
                )
                return redirect(url_for("contact"))
        return render_template("contact.html")

    @app.route("/contact/sms")
    def contact_sms():
        href = _sms_href(app.config.get("SHOP_PHONE", ""))
        if not href:
            flash("문자 문의가 아직 준비되지 않았어요.", "error")
            return redirect(url_for("contact"))
        return redirect(href)

    @app.route("/contact/email")
    def contact_email():
        href = _mailto_href(app.config.get("SHOP_EMAIL", ""))
        if not href:
            flash("이메일 문의가 아직 준비되지 않았어요.", "error")
            return redirect(url_for("contact"))
        return redirect(href)

    with app.app_context():
        db.create_all()
        _ensure_product_columns()
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
