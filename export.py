"""네이버 스마트스토어 / 쿠팡 윙 대량등록용 CSV 생성."""

from __future__ import annotations

import csv
import io
from typing import Iterable

from models import Product


def _image_for_export(product: Product, base_url: str = "") -> str:
    if product.image_url:
        return product.image_url
    if product.image_path and base_url:
        return f"{base_url.rstrip('/')}/static/{product.image_path}"
    if product.image_path:
        return product.image_path
    return ""


def products_to_naver_csv(products: Iterable[Product], base_url: str = "") -> str:
    """스마트스토어 공식 양식이 자주 바뀌므로, 복사하기 쉬운 공통 컬럼 CSV."""
    buf = io.StringIO()
    buf.write("\ufeff")  # Excel 한글용 BOM
    writer = csv.writer(buf)
    writer.writerow(
        [
            "판매자상품코드",
            "상품명",
            "판매가",
            "재고수량",
            "카테고리",
            "색상",
            "옵션명",
            "옵션값",
            "상품상세설명",
            "대표이미지",
            "판매채널메모",
        ]
    )
    for p in products:
        writer.writerow(
            [
                p.slug,
                p.name,
                p.price,
                p.stock,
                p.category,
                p.color,
                "사이즈",
                "/".join(p.size_list()),
                (p.description or "").replace("\n", " "),
                _image_for_export(p, base_url),
                p.channel_note or "",
            ]
        )
    return buf.getvalue()


def products_to_coupang_csv(products: Iterable[Product], base_url: str = "") -> str:
    """쿠팡 윙 대량등록에 맞춰 컬럼을 옮기기 쉬운 CSV."""
    buf = io.StringIO()
    buf.write("\ufeff")
    writer = csv.writer(buf)
    writer.writerow(
        [
            "판매자상품코드",
            "등록상품명",
            "판매가격",
            "재고수량",
            "카테고리메모",
            "옵션타입",
            "옵션값",
            "상품설명",
            "이미지URL",
            "판매채널메모",
        ]
    )
    for p in products:
        writer.writerow(
            [
                p.slug,
                p.name,
                p.price,
                p.stock,
                p.category,
                "사이즈",
                ",".join(p.size_list()),
                (p.description or "").replace("\n", " "),
                _image_for_export(p, base_url),
                p.channel_note or "",
            ]
        )
    return buf.getvalue()
