import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# Render 등에서는 디스크가 임시라, DATA_DIR로 DB/업로드 위치를 바꿀 수 있음
DATA_DIR = Path(os.environ.get("DATA_DIR", BASE_DIR))
DATA_DIR.mkdir(parents=True, exist_ok=True)


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "tokkiyasa-dev-secret-change-me")
    _db_url = os.environ.get("DATABASE_URL")
    if _db_url and _db_url.startswith("postgres://"):
        # SQLAlchemy는 postgresql:// 형식을 씀
        _db_url = _db_url.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_DATABASE_URI = _db_url or f"sqlite:///{DATA_DIR / 'tokkiyasa.db'}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TEMPLATES_AUTO_RELOAD = True
    SEND_FILE_MAX_AGE_DEFAULT = 0
    UPLOAD_FOLDER = Path(os.environ.get("UPLOAD_FOLDER", BASE_DIR / "static" / "uploads"))
    MAX_CONTENT_LENGTH = 8 * 1024 * 1024
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

    # 토스페이먼츠 — 나중에 실결제 연결 시 환경변수로 넣으세요
    TOSS_CLIENT_KEY = os.environ.get("TOSS_CLIENT_KEY", "")
    TOSS_SECRET_KEY = os.environ.get("TOSS_SECRET_KEY", "")
    PAYMENT_MODE = os.environ.get("PAYMENT_MODE", "bank")  # bank | demo | toss

    # 무통장 입금 계좌 (홈·주문 화면에 표시)
    SHOP_BANK_NAME = os.environ.get("SHOP_BANK_NAME", "신한은행")
    SHOP_BANK_ACCOUNT = os.environ.get("SHOP_BANK_ACCOUNT", "110-279-489620")
    SHOP_BANK_HOLDER = os.environ.get("SHOP_BANK_HOLDER", "박재형")
    SHOP_BANK_NOTE = os.environ.get(
        "SHOP_BANK_NOTE",
        "입금자명을 주문자 성함과 같게 적어 주세요. 입금 확인 후 발송합니다.",
    )

    ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
    # Render에 예전에 생성된 랜덤 ADMIN_PASSWORD가 남아 있어도
    # 기본값으로 맞춰 로그인이 되게 합니다. (나중에 바꾸려면 ADMIN_PASSWORD_LOCK=0)
    _admin_pw = os.environ.get("ADMIN_PASSWORD", "danangsali123")
    if os.environ.get("ADMIN_PASSWORD_LOCK", "1") != "0":
        _admin_pw = "danangsali123"
    ADMIN_PASSWORD = _admin_pw
    SHOP_NAME = "다낭살이"

    # 고객센터 연락처 (사이트에 표시)
    SHOP_PHONE = os.environ.get("SHOP_PHONE", "010-6306-1092")
    SHOP_KAKAO = os.environ.get("SHOP_KAKAO", "akkop78@gmail.com")
    SHOP_EMAIL = os.environ.get("SHOP_EMAIL", "akkop78@gmail.com")
    SHOP_HOURS = os.environ.get(
        "SHOP_HOURS", "평일 10:00–18:00 (베트남 시간, 주말·공휴일 휴무)"
    )

    # 주문/문의 알림 받을 이메일
    ADMIN_NOTIFY_EMAIL = os.environ.get(
        "ADMIN_NOTIFY_EMAIL",
        os.environ.get("SHOP_EMAIL", "akkop78@gmail.com"),
    )

    # 선택: 지메일 등 SMTP (설정하면 주문 시 메일 발송)
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", "587"))
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", "")
    MAIL_SENDER = os.environ.get("MAIL_SENDER", "")
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "1") != "0"

    # 선택: 디스코드 웹훅 (폰 알림용)
    DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "")

    # 폰 푸시 알림 (ntfy.sh) — 앱에서 같은 주제를 구독하면 주문 시 알림
    # https://ntfy.sh 앱 설치 후 아래 주제를 구독하세요
    NTFY_TOPIC = os.environ.get("NTFY_TOPIC", "danangsali-akkop78-orders")
    NTFY_SERVER = os.environ.get("NTFY_SERVER", "https://ntfy.sh")
