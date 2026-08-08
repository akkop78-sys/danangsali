from __future__ import annotations

from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()

# 무통장 흐름: 입금대기 → 입금확인 → 배송준비 → 배송중 → 완료
ORDER_STATUSES = (
    "입금대기",
    "입금확인",
    "배송준비",
    "배송중",
    "완료",
    "취소",
    "접수",  # 이전 주문 호환
)
CATEGORIES = ["전체", "세트"]


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(80), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    orders = db.relationship("Order", back_populates="user", lazy=True)

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(80), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    stock = db.Column(db.Integer, default=0, nullable=False)
    category = db.Column(db.String(40), nullable=False)
    color = db.Column(db.String(40), default="")
    description = db.Column(db.Text, default="")
    detail_html = db.Column(db.Text, default="")  # 상세페이지 연출용 HTML
    sizes = db.Column(db.String(120), default="FREE")  # comma-separated
    image_url = db.Column(db.String(500), default="")
    image_path = db.Column(db.String(255), default="")  # relative under static/
    channel_note = db.Column(db.String(255), default="")
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def size_list(self) -> list[str]:
        return [s.strip() for s in (self.sizes or "FREE").split(",") if s.strip()]

    def display_image(self) -> str:
        if self.image_path:
            return self.image_path
        return self.image_url or ""


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    buyer_name = db.Column(db.String(80), nullable=False)
    buyer_phone = db.Column(db.String(40), nullable=False)
    buyer_address = db.Column(db.Text, nullable=False)
    total = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default="접수", nullable=False)
    payment_mode = db.Column(db.String(20), default="demo")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="orders")
    items = db.relationship(
        "OrderItem", back_populates="order", cascade="all, delete-orphan", lazy=True
    )


class OrderItem(db.Model):
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=True)
    product_name = db.Column(db.String(120), nullable=False)
    size = db.Column(db.String(20), default="FREE")
    qty = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Integer, nullable=False)

    order = db.relationship("Order", back_populates="items")
    product = db.relationship("Product")

    @property
    def line_total(self) -> int:
        return self.unit_price * self.qty


class Inquiry(db.Model):
    """고객센터 문의 (상품 이상·배송 문의 등)."""

    __tablename__ = "inquiries"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    phone = db.Column(db.String(40), default="")
    email = db.Column(db.String(120), default="")
    order_ref = db.Column(db.String(40), default="")  # 주문번호 참고용
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
