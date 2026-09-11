"""Cached SiteSetting accessor. Invalidate on admin edit."""
import re

from app.extensions import db
from app.models import SiteSetting

DEFAULT_CONTACT_PHONE = "000-0000-0000"
DEFAULT_CONTACT_HOURS = "24시간 상담 가능"

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


def get_contact_phone() -> str:
    """고객센터 전화번호. 어드민 설정에서 수시로 변경 가능."""
    return get("contact_phone", DEFAULT_CONTACT_PHONE)


def get_contact_phone_tel() -> str:
    """tel: 링크용 — 숫자만 남긴 전화번호."""
    return re.sub(r"\D", "", get_contact_phone())


def get_contact_hours() -> str:
    return get("contact_hours", DEFAULT_CONTACT_HOURS)
