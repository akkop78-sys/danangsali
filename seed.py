from models import OrderItem, Product, User, db

SAMPLE_PRODUCTS = [
    {
        "slug": "danang-daily",
        "name": "다낭 데일리 팬티",
        "price": 18000,
        "stock": 80,
        "category": "팬티",
        "color": "아이보리",
        "description": "베트남 다낭에서 고른 데일리용. 부드러운 면 혼방으로 하루 종일 편안해요. 라인 없이 자연스럽게 붙습니다.",
        "sizes": "S,M,L,XL",
        "image_url": "https://images.unsplash.com/photo-1562157873-818bc0726f68?auto=format&fit=crop&w=900&q=80",
        "channel_note": "베스트",
    },
    {
        "slug": "danang-soft",
        "name": "다낭 소프트 코튼",
        "price": 19000,
        "stock": 70,
        "category": "팬티",
        "color": "베이지",
        "description": "살결에 닿는 촉감이 특히 좋은 소프트 코튼. 땀 끼는 분께 추천해요.",
        "sizes": "S,M,L,XL",
        "image_url": "https://images.unsplash.com/photo-1558171813-4c088753af8f?auto=format&fit=crop&w=900&q=80",
        "channel_note": "추천",
    },
    {
        "slug": "danang-seamless",
        "name": "심리스 에어 팬티",
        "price": 22000,
        "stock": 60,
        "category": "팬티",
        "color": "누드",
        "description": "봉제선이 거의 없어 레깅스·원피스 아래에서도 티가 덜 나요. 가볍고 시원한 착용감.",
        "sizes": "S,M,L",
        "image_url": "https://images.unsplash.com/photo-1489987707025-afc232f7ea0f?auto=format&fit=crop&w=900&q=80",
    },
    {
        "slug": "danang-lace",
        "name": "레이스 엣지 팬티",
        "price": 24000,
        "stock": 45,
        "category": "팬티",
        "color": "소프트핑크",
        "description": "가장자리만 은은한 레이스. 과하지 않고 단정한 포인트로, 선물용으로도 좋아요.",
        "sizes": "S,M,L",
        "image_url": "https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?auto=format&fit=crop&w=900&q=80",
    },
    {
        "slug": "danang-trio",
        "name": "다낭 팬티 3매 세트",
        "price": 49000,
        "stock": 50,
        "category": "세트",
        "color": "믹스",
        "description": "가장 많이 찾는 구성. 데일리·소프트·심리스를 골고루 담은 실속 세트입니다.",
        "sizes": "S,M,L,XL",
        "image_url": "https://images.unsplash.com/photo-1441986300917-64674bd600d8?auto=format&fit=crop&w=900&q=80",
        "channel_note": "세트특가",
    },
    {
        "slug": "danang-week",
        "name": "일주일 팬티 팩 (7매)",
        "price": 98000,
        "stock": 35,
        "category": "세트",
        "color": "뉴트럴",
        "description": "매일 갈아입기 좋은 7매 팩. 베트남에서 검수 후 보내 드려요.",
        "sizes": "S,M,L,XL",
        "image_url": "https://images.unsplash.com/photo-1523381210434-271e8be1f52b?auto=format&fit=crop&w=900&q=80",
    },
    {
        "slug": "danang-bralette",
        "name": "소프트 브라렛",
        "price": 32000,
        "stock": 40,
        "category": "브라탑",
        "color": "샌드",
        "description": "와이어 없이 편안하게. 팬티와 톤을 맞춰 입은 브라렛입니다.",
        "sizes": "S,M,L",
        "image_url": "https://images.unsplash.com/photo-1434389677669-e08b4cac3105?auto=format&fit=crop&w=900&q=80",
    },
    {
        "slug": "danang-set-match",
        "name": "매치 브라렛+팬티 세트",
        "price": 52000,
        "stock": 30,
        "category": "세트",
        "color": "아이보리",
        "description": "브라렛과 팬티를 한 세트로. 처음 다낭팬티를 경험하기 좋은 구성이에요.",
        "sizes": "S,M,L",
        "image_url": "https://images.unsplash.com/photo-1490481651871-ab68de25d43d?auto=format&fit=crop&w=900&q=80",
        "channel_note": "입문세트",
    },
]


def _needs_catalog_refresh() -> bool:
    if Product.query.count() == 0:
        return True
    if Product.query.filter_by(slug="soft-tee").first():
        return True
    if not Product.query.filter_by(slug="danang-daily").first():
        return True
    return False


def _refresh_danang_catalog() -> None:
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
        _refresh_danang_catalog()

    db.session.commit()
