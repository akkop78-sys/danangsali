from models import OrderItem, Product, User, db

SAMPLE_PRODUCTS = [
    {
        "slug": "jewel-panty-10",
        "name": "보석팬티 10개 세트",
        "price": 30000,
        "stock": 50,
        "category": "세트",
        "color": "누드베이지",
        "description": "다낭 한시장에서 유명한 보석팬티 10개 세트. 가운데 큐빅(보석) 포인트가 있는 심리스 스타일로, 데일리·선물용으로 많이 찾습니다.",
        "sizes": "FREE",
        "image_url": "",
        "image_path": "uploads/jewel-panty-set.jpg",
        "channel_note": "보석팬티",
    },
    {
        "slug": "jiller-panty-10",
        "name": "질러팬티 10개 세트",
        "price": 35000,
        "stock": 50,
        "category": "세트",
        "color": "누드/핑크",
        "description": "다낭·나트랑 시장에서 인기인 질러팬티 10개 세트. 안 입은 듯 부드러운 아이스실크 심리스로, 걸이형 낱장·세트 구성입니다.",
        "sizes": "FREE",
        "image_url": "",
        "image_path": "uploads/jiller-panty-set.jpg",
        "channel_note": "질러팬티",
    },
]


def _needs_catalog_refresh() -> bool:
    if Product.query.count() != len(SAMPLE_PRODUCTS):
        return True
    for item in SAMPLE_PRODUCTS:
        p = Product.query.filter_by(slug=item["slug"]).first()
        if not p:
            return True
        if (
            p.image_path != item.get("image_path", "")
            or p.price != item["price"]
            or p.description != item["description"]
        ):
            return True
    return False


def _refresh_catalog() -> None:
    new_slugs = {item["slug"] for item in SAMPLE_PRODUCTS}

    for item in SAMPLE_PRODUCTS:
        existing = Product.query.filter_by(slug=item["slug"]).first()
        if existing:
            for key, value in item.items():
                setattr(existing, key, value)
            existing.is_active = True
        else:
            db.session.add(Product(**item))

    for product in Product.query.all():
        if product.slug in new_slugs:
            continue
        linked = OrderItem.query.filter_by(product_id=product.id).first()
        if linked:
            product.is_active = False
        else:
            db.session.delete(product)


def seed_database(admin_username: str, admin_password: str) -> None:
    if not User.query.filter_by(email=f"{admin_username}@tokkiyasa.local").first():
        admin = User(
            email=f"{admin_username}@tokkiyasa.local",
            name="관리자",
            is_admin=True,
        )
        admin.set_password(admin_password)
        db.session.add(admin)

    if _needs_catalog_refresh():
        _refresh_catalog()

    db.session.commit()
