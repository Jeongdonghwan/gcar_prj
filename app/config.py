import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
INSTANCE_DIR = BASE_DIR / "instance"
load_dotenv(INSTANCE_DIR / ".env")


class BaseConfig:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me")

    DB_USER = os.environ.get("DB_USER", "garage")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
    DB_HOST = os.environ.get("DB_HOST", "127.0.0.1")
    DB_PORT = os.environ.get("DB_PORT", "3306")
    DB_NAME = os.environ.get("DB_NAME", "garage")
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        "?charset=utf8mb4"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 3600,
    }

    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB
    UPLOAD_ROOT = BASE_DIR / "app" / "static" / "uploads"
    UPLOAD_TMP_DIR = UPLOAD_ROOT / "_tmp"
    UPLOAD_VEHICLES_DIR = UPLOAD_ROOT / "vehicles"
    UPLOAD_BRANDS_DIR = UPLOAD_ROOT / "brands"
    ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    WTF_CSRF_TIME_LIMIT = 60 * 60 * 8  # 8h

    KAKAO_REST_API_KEY = os.environ.get("KAKAO_REST_API_KEY", "")
    KAKAO_REDIRECT_URI = os.environ.get(
        "KAKAO_REDIRECT_URI", "http://localhost:5000/auth/kakao/callback"
    )


class DevConfig(BaseConfig):
    DEBUG = True
    SESSION_COOKIE_SECURE = False


class ProdConfig(BaseConfig):
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    PREFERRED_URL_SCHEME = "https"


class TestConfig(BaseConfig):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
