import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

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
    UPLOAD_FOLDER = Path(os.environ.get("UPLOAD_FOLDER", BASE_DIR / "static" / "uploads"))
    MAX_CONTENT_LENGTH = 8 * 1024 * 1024
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

    # 토스페이먼츠 — 나중에 실결제 연결 시 환경변수로 넣으세요
    TOSS_CLIENT_KEY = os.environ.get("TOSS_CLIENT_KEY", "")
    TOSS_SECRET_KEY = os.environ.get("TOSS_SECRET_KEY", "")
    PAYMENT_MODE = os.environ.get("PAYMENT_MODE", "demo")  # demo | toss

    ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "tokkiyasa123")
    SHOP_NAME = "다낭살이"
