from __future__ import annotations

import re
import uuid
from functools import wraps
from pathlib import Path

from flask import (
    Blueprint,
    Response,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.utils import secure_filename

from export import products_to_coupang_csv, products_to_naver_csv
from models import CATEGORIES, ORDER_STATUSES, Inquiry, Order, Product, User, db

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user_id = session.get("user_id")
        if not user_id:
            flash("관리자 로그인이 필요해요.", "error")
            return redirect(url_for("admin.login"))
        user = User.query.get(user_id)
        if not user or not user.is_admin:
            flash("관리자만 접근할 수 있어요.", "error")
            return redirect(url_for("admin.login"))
        return view(*args, **kwargs)

    return wrapped


def _slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)
    text = re.sub(r"[-\s]+", "-", text)
    return text[:70] or f"item-{uuid.uuid4().hex[:8]}"


def _unique_slug(base: str, product_id: int | None = None) -> str:
    slug = _slugify(base)
    candidate = slug
    n = 2
    while True:
        q = Product.query.filter_by(slug=candidate)
        if product_id:
            q = q.filter(Product.id != product_id)
        if not q.first():
            return candidate
        candidate = f"{slug}-{n}"
        n += 1


def _allowed_file(filename: str) -> bool:
    allowed = current_app.config["ALLOWED_EXTENSIONS"]
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed


def _save_upload(file_storage) -> str:
    if not file_storage or not file_storage.filename:
        return ""
    if not _allowed_file(file_storage.filename):
        raise ValueError("이미지 파일만 올릴 수 있어요. (png, jpg, jpeg, gif, webp)")
    upload_dir: Path = current_app.config["UPLOAD_FOLDER"]
    upload_dir.mkdir(parents=True, exist_ok=True)
    original = secure_filename(file_storage.filename)
    name = f"{uuid.uuid4().hex}_{original}"
    path = upload_dir / name
    file_storage.save(path)
    return f"uploads/{name}"


def _product_from_form(product: Product | None = None) -> Product:
    product = product or Product()
    name = request.form.get("name", "").strip()
    if not name:
        raise ValueError("상품명을 입력해 주세요.")

    price = int(request.form.get("price") or 0)
    stock = int(request.form.get("stock") or 0)
    if price < 0 or stock < 0:
        raise ValueError("가격과 재고는 0 이상이어야 해요.")

    slug_input = request.form.get("slug", "").strip() or name
    product.name = name
    product.slug = _unique_slug(slug_input, product.id if product.id else None)
    product.price = price
    product.stock = stock
    product.category = request.form.get("category", "상의").strip() or "상의"
    product.color = request.form.get("color", "").strip()
    product.description = request.form.get("description", "").strip()
    product.detail_html = request.form.get("detail_html", "").strip()
    sizes = request.form.get("sizes", "FREE").strip() or "FREE"
    product.sizes = ",".join(s.strip() for s in sizes.replace("/", ",").split(",") if s.strip())
    product.channel_note = request.form.get("channel_note", "").strip()
    product.is_active = request.form.get("is_active") == "on"

    image_url = request.form.get("image_url", "").strip()
    if image_url:
        product.image_url = image_url

    try:
        uploaded = _save_upload(request.files.get("image_file"))
        if uploaded:
            product.image_path = uploaded
    except ValueError:
        raise

    if not product.image_url and not product.image_path:
        raise ValueError("이미지 URL을 넣거나 사진을 업로드해 주세요.")

    return product


@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        email = f"{username}@tokkiyasa.local"
        user = User.query.filter_by(email=email, is_admin=True).first()
        if user and user.check_password(password):
            session["user_id"] = user.id
            session["is_admin"] = True
            flash("관리자로 로그인했어요.", "success")
            return redirect(url_for("admin.dashboard"))
        flash("아이디 또는 비밀번호가 올바르지 않아요.", "error")
    return render_template("admin/login.html")


@admin_bp.route("/logout")
def logout():
    session.pop("user_id", None)
    session.pop("is_admin", None)
    flash("로그아웃했어요.", "success")
    return redirect(url_for("admin.login"))


@admin_bp.route("/")
@admin_required
def dashboard():
    products = Product.query.order_by(Product.id.desc()).all()
    orders = Order.query.order_by(Order.created_at.desc()).limit(8).all()
    low_stock = Product.query.filter(Product.stock <= 5, Product.is_active.is_(True)).count()
    pending_orders = Order.query.filter_by(status="접수").count()
    unread_inquiries = Inquiry.query.filter_by(is_read=False).count()
    return render_template(
        "admin/dashboard.html",
        products=products,
        orders=orders,
        product_count=len(products),
        order_count=Order.query.count(),
        low_stock=low_stock,
        pending_orders=pending_orders,
        unread_inquiries=unread_inquiries,
        ntfy_topic=current_app.config.get("NTFY_TOPIC", ""),
    )


@admin_bp.route("/products")
@admin_required
def products():
    items = Product.query.order_by(Product.id.desc()).all()
    return render_template("admin/products.html", products=items)


@admin_bp.route("/products/new", methods=["GET", "POST"])
@admin_required
def product_new():
    if request.method == "POST":
        try:
            product = _product_from_form()
            db.session.add(product)
            db.session.commit()
            flash("상품을 등록했어요.", "success")
            return redirect(url_for("admin.products"))
        except (ValueError, TypeError) as exc:
            db.session.rollback()
            flash(str(exc), "error")
    return render_template(
        "admin/product_form.html",
        product=None,
        categories=[c for c in CATEGORIES if c != "전체"],
    )


@admin_bp.route("/products/<int:product_id>/edit", methods=["GET", "POST"])
@admin_required
def product_edit(product_id: int):
    product = Product.query.get_or_404(product_id)
    if request.method == "POST":
        try:
            _product_from_form(product)
            db.session.commit()
            flash("상품을 수정했어요.", "success")
            return redirect(url_for("admin.products"))
        except (ValueError, TypeError) as exc:
            db.session.rollback()
            flash(str(exc), "error")
    return render_template(
        "admin/product_form.html",
        product=product,
        categories=[c for c in CATEGORIES if c != "전체"],
    )


@admin_bp.route("/products/<int:product_id>/delete", methods=["POST"])
@admin_required
def product_delete(product_id: int):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash("상품을 삭제했어요.", "success")
    return redirect(url_for("admin.products"))


@admin_bp.route("/orders")
@admin_required
def orders():
    items = Order.query.order_by(Order.created_at.desc()).all()
    return render_template("admin/orders.html", orders=items, statuses=ORDER_STATUSES)


@admin_bp.route("/inquiries")
@admin_required
def inquiries():
    items = Inquiry.query.order_by(Inquiry.created_at.desc()).all()
    return render_template("admin/inquiries.html", inquiries=items)


@admin_bp.route("/inquiries/<int:inquiry_id>/read", methods=["POST"])
@admin_required
def inquiry_read(inquiry_id: int):
    inquiry = Inquiry.query.get_or_404(inquiry_id)
    inquiry.is_read = True
    db.session.commit()
    flash("문의를 확인 처리했어요.", "success")
    return redirect(url_for("admin.inquiries"))


@admin_bp.route("/orders/<int:order_id>/status", methods=["POST"])
@admin_required
def order_status(order_id: int):
    order = Order.query.get_or_404(order_id)
    status = request.form.get("status", "")
    if status not in ORDER_STATUSES:
        flash("잘못된 상태예요.", "error")
        return redirect(url_for("admin.orders"))
    order.status = status
    db.session.commit()
    flash(f"주문 #{order.id} 상태를 '{status}'(으)로 바꿨어요.", "success")
    return redirect(url_for("admin.orders"))


@admin_bp.route("/export")
@admin_required
def export_page():
    count = Product.query.filter_by(is_active=True).count()
    return render_template("admin/export.html", product_count=count)


@admin_bp.route("/export/naver.csv")
@admin_required
def export_naver():
    products = Product.query.filter_by(is_active=True).order_by(Product.id).all()
    base_url = request.url_root.rstrip("/")
    csv_data = products_to_naver_csv(products, base_url=base_url)
    return Response(
        csv_data,
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=tokkiyasa_naver.csv"},
    )


@admin_bp.route("/export/coupang.csv")
@admin_required
def export_coupang():
    products = Product.query.filter_by(is_active=True).order_by(Product.id).all()
    base_url = request.url_root.rstrip("/")
    csv_data = products_to_coupang_csv(products, base_url=base_url)
    return Response(
        csv_data,
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=tokkiyasa_coupang.csv"},
    )


@admin_bp.route("/guide")
@admin_required
def guide():
    return render_template("admin/guide.html")


@admin_bp.route("/password", methods=["GET", "POST"])
@admin_required
def change_password():
    if request.method == "POST":
        current = request.form.get("current_password", "")
        new1 = request.form.get("new_password", "")
        new2 = request.form.get("new_password2", "")
        user = User.query.get(session["user_id"])
        if not user or not user.check_password(current):
            flash("현재 비밀번호가 틀려요.", "error")
        elif len(new1) < 6:
            flash("새 비밀번호는 6자 이상으로 해 주세요.", "error")
        elif new1 != new2:
            flash("새 비밀번호가 서로 달라요.", "error")
        else:
            user.set_password(new1)
            db.session.commit()
            flash("비밀번호를 바꿨어요.", "success")
            return redirect(url_for("admin.dashboard"))
    return render_template("admin/password.html")
