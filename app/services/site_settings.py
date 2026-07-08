"""Cached SiteSetting accessor. Invalidate on admin edit."""
from flask import current_app
from app.extensions import db
from app.models import SiteSetting

_cache: dict[str, str] = {}


def _load(key: str) -> str | None:
    if key in _cache:
        return _cache[key]
    row = db.session.get(SiteSetting, key)
    if row and row.value:
        _cache[key] = row.value
        return row.value
    return None


def invalidate(key: str | None = None) -> None:
    if key is None:
        _cache.clear()
    else:
        _cache.pop(key, None)


def get(key: str, default: str = "") -> str:
    try:
        value = _load(key)
    except Exception:
        return default
    return value if value is not None else default


def set_value(key: str, value: str) -> None:
    row = db.session.get(SiteSetting, key)
    if row is None:
        row = SiteSetting(key=key, value=value)
        db.session.add(row)
    else:
        row.value = value
    db.session.commit()
    invalidate(key)


def get_kakao_channel_url() -> str:
    val = get("kakao_channel_url", "")
    if val:
        return val
    # Fallback to env-set value (Sprint 1 dev)
    try:
        return current_app.config.get("KAKAO_CHANNEL_URL_FALLBACK", "")
    except RuntimeError:
        return ""
