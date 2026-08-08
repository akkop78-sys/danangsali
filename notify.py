"""주문·문의 알림. 이메일/디스코드가 설정돼 있으면 보내고, 없으면 파일에만 기록합니다."""

from __future__ import annotations

import json
import smtplib
import urllib.error
import urllib.request
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path

from flask import current_app


def _log_dir() -> Path:
    from config import DATA_DIR

    path = Path(DATA_DIR) / "notifications"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _append_log(kind: str, body: str) -> None:
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{stamp}] {kind}\n{body}\n{'-' * 40}\n"
    (_log_dir() / "events.log").open("a", encoding="utf-8").write(line)


def _send_email(subject: str, body: str) -> bool:
    to_addr = (current_app.config.get("ADMIN_NOTIFY_EMAIL") or "").strip()
    host = (current_app.config.get("MAIL_SERVER") or "").strip()
    if not to_addr or not host:
        return False

    port = int(current_app.config.get("MAIL_PORT") or 587)
    user = (current_app.config.get("MAIL_USERNAME") or "").strip()
    password = current_app.config.get("MAIL_PASSWORD") or ""
    sender = (current_app.config.get("MAIL_SENDER") or user or to_addr).strip()
    use_tls = bool(current_app.config.get("MAIL_USE_TLS", True))

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = to_addr
    msg.set_content(body)

    try:
        with smtplib.SMTP(host, port, timeout=20) as smtp:
            if use_tls:
                smtp.starttls()
            if user and password:
                smtp.login(user, password)
            smtp.send_message(msg)
        return True
    except Exception as exc:  # noqa: BLE001 — 알림 실패해도 주문은 유지
        _append_log("email-error", f"{subject}\n{exc}")
        return False


def _send_discord(content: str) -> bool:
    url = (current_app.config.get("DISCORD_WEBHOOK_URL") or "").strip()
    if not url:
        return False
    payload = json.dumps({"content": content[:1900]}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json", "User-Agent": "danangsali-shop"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return 200 <= resp.status < 300
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        _append_log("discord-error", f"{exc}\n{content}")
        return False


def _send_ntfy(title: str, body: str) -> bool:
    """무료 폰 푸시 (ntfy.sh). 메일 설정 없이도 알림 가능."""
    topic = (current_app.config.get("NTFY_TOPIC") or "").strip()
    if not topic:
        return False
    server = (current_app.config.get("NTFY_SERVER") or "https://ntfy.sh").rstrip("/")
    url = f"{server}/{topic}"
    # 제목은 본문 첫 줄에도 넣고, 헤더는 ASCII만 사용
    message = f"{title}\n\n{body}".encode("utf-8")
    req = urllib.request.Request(
        url,
        data=message,
        method="POST",
        headers={
            "Title": "DanangSali",
            "Priority": "high",
            "Tags": "shopping_cart",
            "Content-Type": "text/plain; charset=utf-8",
            "User-Agent": "danangsali-shop",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            ok = 200 <= resp.status < 300
            if ok:
                _append_log("ntfy-ok", f"{title}\n{body[:200]}")
            return ok
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        _append_log("ntfy-error", f"{exc}\n{title}\n{body}")
        return False


def notify_new_order(order) -> None:
    items = "\n".join(
        f"- {item.product_name} / {item.size} / {item.qty}개 / {item.unit_price:,}원"
        for item in order.items
    )
    body = (
        f"새 주문이 들어왔습니다.\n"
        f"주문번호: #{order.id}\n"
        f"주문자: {order.buyer_name}\n"
        f"전화: {order.buyer_phone}\n"
        f"주소: {order.buyer_address}\n"
        f"금액: {order.total:,}원\n"
        f"결제: {order.payment_mode}\n"
        f"상태: {order.status}\n\n"
        f"[상품]\n{items}\n\n"
        f"관리자 → 주문 메뉴에서 확인 후 포장·발송하세요."
    )
    _append_log("order", body)
    shop = current_app.config.get("SHOP_NAME", "다낭살이")
    title = f"[{shop}] 새 주문 #{order.id}"
    mailed = _send_email(title, body)
    discord = _send_discord(f"🛒 **{title}**\n{body}")
    ntfy = _send_ntfy(title, body)
    _append_log(
        "order-notify-result",
        f"email={mailed} discord={discord} ntfy={ntfy}",
    )


def notify_new_inquiry(inquiry) -> None:
    body = (
        f"고객 문의가 도착했습니다.\n"
        f"이름: {inquiry.name}\n"
        f"전화: {inquiry.phone}\n"
        f"이메일: {inquiry.email}\n"
        f"주문번호: {inquiry.order_ref or '-'}\n"
        f"내용:\n{inquiry.message}"
    )
    _append_log("inquiry", body)
    shop = current_app.config.get("SHOP_NAME", "다낭살이")
    title = f"[{shop}] 고객 문의"
    mailed = _send_email(f"{title} — {inquiry.name}", body)
    discord = _send_discord(f"💬 **{title}**\n{body}")
    ntfy = _send_ntfy(title, body)
    _append_log(
        "inquiry-notify-result",
        f"email={mailed} discord={discord} ntfy={ntfy}",
    )
