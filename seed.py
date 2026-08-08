from models import OrderItem, Product, User, db

SAMPLE_PRODUCTS = [
    {
        "slug": "jewel-panty-10",
        "name": "보석팬티 10개 세트",
        "price": 30000,
        "stock": 50,
        "category": "세트",
        "color": "믹스",
        "description": "다낭에서 고른 보석팬티 10개 세트. 데일리로 돌려 입기 좋은 구성입니다.",
        "sizes": "FREE",
        "image_url": "https://images.unsplash.com/photo-1562157873-818bc0726f68?auto=format&fit=crop&w=900&q=80",
        "channel_note": "보석팬티",
    },
    {
        "slug": "jiller-panty-10",
        "name": "질러팬티 10개 세트",
        "price": 35000,
        "stock": 50,
        "category": "세트",
        "color": "믹스",
        "description": "다낭에서 고른 질러팬티 10개 세트. 착용감 좋은 구성으로 구성했습니다.",
        "sizes": "FREE",
        "image_url": "https://images.unsplash.com/photo-1558171813-4c088753af8f?auto=format&fit=crop&w=900&q=80",
        "channel_note": "질러팬티",
    },
]


def _needs_catalog_refresh() -> bool:
    if Product.query.count() != len(SAMPLE_PRODUCTS):
        return True
    slugs = {p.slug for p in Product.query.all()}
    expected = {item["slug"] for item in SAMPLE_PRODUCTS}
    return slugs != expected


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
