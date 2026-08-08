from models import OrderItem, Product, User, db

JEWEL_DETAIL = """
<div class="story-block">
  <h3>구성</h3>
  <p>보석팬티 <strong>10장</strong> 세트 · FREE 사이즈 · 누드·크림·피치 등 살색 계열</p>
  <ul>
    <li>앞면 중앙 큐빅(라인스톤) 세로 라인 — 한시장에서 말하는 그 ‘보석팬티’</li>
    <li>심리스 레이저컷 가장자리로 겉옷에 라인 덜 탐</li>
    <li>데일리·여행·선물용으로 많이 사 가시는 구성입니다</li>
  </ul>
</div>
<div class="story-block">
  <h3>왜 이 상품인가요</h3>
  <p>다낭 한시장에서 한국 손님들이 제일 많이 집는 스타일 중 하나예요.
  사진처럼 가운데 보석 라인이 포인트라, 받아보셨을 때 “아 이거구나” 하실 거예요.</p>
</div>
<div class="story-block story-split">
  <div>
    <h3>현지 검수</h3>
    <p>베트남 주재원 10년+ · 직접 써 보고 만족한 것만 골라 담습니다.
    구멍·오염·심하게 비뚤어진 보석 부착은 걸러내고 포장합니다.</p>
  </div>
  <div>
    <h3>세탁·사용</h3>
    <ul>
      <li>미지근한 물에 손세탁 권장 (큐빅 보호)</li>
      <li>강한 세제·건조기·표백제 피해주세요</li>
      <li>그늘에서 뉘어 말리면 형태가 오래가요</li>
    </ul>
  </div>
</div>
<div class="story-block">
  <h3>배송 안내</h3>
  <p>주문 확인 후 현지에서 포장·발송합니다. 일정은 주문 후 문자/톡으로 안내드려요.
  급하시면 문의로 “희망 일정”만 적어 주세요.</p>
</div>
"""

JILLER_DETAIL = """
<div class="story-block">
  <h3>구성</h3>
  <p>질러팬티 <strong>10장</strong> 세트 · FREE 사이즈 · 누드·크림·연그레이 등 실은색 위주</p>
  <ul>
    <li>허리에 골드 각인 <strong>GILLER PRIZE</strong> 로고 — 시장에서 부르는 ‘질러팬티’</li>
    <li>물결형 레이저컷 가장자리 · 안 입은 듯한 심리스 느낌</li>
    <li>고탄력 아이스실크에 가까운 촉감으로 여름·땀 많은 날에도 편해요</li>
  </ul>
</div>
<figure class="story-figure">
  <img src="/static/uploads/jiller-market-mix.jpg" alt="다낭 한시장 질러팬티 실물" />
  <figcaption>한시장에서 흔히 보이는 질러·심리스 실물 예시 (브랜드 택 포함)</figcaption>
</figure>
<div class="story-block">
  <h3>왜 이 상품인가요</h3>
  <p>다낭·나트랑 시장 단골 아이템이에요. “안 입은 것 같다”는 후기가 많은 이유가
  얇고 부드러운 원단 + 라인 안 타는 마감 때문입니다. 세트라 색 섞어 쓰시기 좋아요.</p>
</div>
<div class="story-block story-split">
  <div>
    <h3>현지 검수</h3>
    <p>주재원이 매장·시장에서 상태 보고 고릅니다.
    로고 인쇄 번짐, 올풀림, 심한 이색은 빼고 보냅니다.</p>
  </div>
  <div>
    <h3>세탁·사용</h3>
    <ul>
      <li>찬물·미온수 손세탁 또는 망에 넣어 약하게</li>
      <li>건조기·다리미 금지</li>
      <li>짙은 색과 따로 세탁하면 이염을 줄일 수 있어요</li>
    </ul>
  </div>
</div>
<div class="story-block">
  <h3>배송 안내</h3>
  <p>주문 확인 → 현지 포장 → 발송 순입니다. 일정은 주문 후 안내드리며,
  보석팬티와 함께 시키시면 한 번에 묶어 보내드려요.</p>
</div>
"""

SAMPLE_PRODUCTS = [
    {
        "slug": "jewel-panty-10",
        "name": "보석팬티 10개 세트",
        "price": 30000,
        "stock": 50,
        "category": "세트",
        "color": "누드/크림/피치",
        "description": "다낭 한시장에서 유명한 보석팬티 10개 세트. 앞면 중앙 큐빅(라인스톤) 세로 라인이 포인트인 심리스 스타일로, 데일리·선물용으로 많이 찾습니다.",
        "detail_html": JEWEL_DETAIL.strip(),
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
        "color": "누드/크림/연그레이",
        "description": "다낭·나트랑 시장 인기 질러팬티 10개 세트. 허리 GILLER PRIZE 로고, 물결형 레이저컷 심리스로 안 입은 듯 부드럽습니다.",
        "detail_html": JILLER_DETAIL.strip(),
        "sizes": "FREE",
        "image_url": "",
        "image_path": "uploads/jiller-panty-set.jpg",
        "channel_note": "질러팬티",
    },
]


def _needs_catalog_refresh() -> bool:
    new_slugs = {item["slug"] for item in SAMPLE_PRODUCTS}
    extras = Product.query.filter(~Product.slug.in_(new_slugs)).count()
    if extras:
        return True
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
            or (p.detail_html or "") != item.get("detail_html", "")
            or p.color != item.get("color", "")
            or not p.is_active
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
