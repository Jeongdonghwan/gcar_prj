from datetime import datetime


def format_price_man(min_man, max_man=None) -> str:
    """가격 포맷. price_min_man만 있으면 '월 239만원', max가 다르면 범위.

    None이거나 0이면 빈 문자열.
    """
    if not min_man:
        return ""
    if max_man and max_man != min_man:
        return f"월 {min_man:,}~{max_man:,}만원"
    return f"월 {min_man:,}만원"


def format_new_price_man(value) -> str:
    if not value:
        return ""
    return f"신차가 {value:,}만원"


def format_mileage(value) -> str:
    if value is None:
        return ""
    return f"{value:,}km"


def format_date_kr(value: datetime) -> str:
    if not value:
        return ""
    return value.strftime("%Y.%m.%d")


def fuel_label(value: str) -> str:
    mapping = {
        "gasoline": "가솔린",
        "diesel": "디젤",
        "hybrid": "하이브리드",
        "ev": "전기",
        "lpg": "LPG",
    }
    return mapping.get(value, value or "")


def product_type_label(value: str) -> str:
    mapping = {"subscription": "구독", "rent": "렌트", "super": "슈퍼카"}
    return mapping.get(value, value or "")


def faq_category_label(value: str) -> str:
    mapping = {
        "signup": "가입",
        "vehicle": "차량",
        "subscription": "구독",
        "insurance": "보험",
        "inspection": "점검",
        "return": "반납",
        "etc": "기타",
    }
    return mapping.get(value, value or "")


def register_filters(app):
    app.jinja_env.filters["price_man"] = format_price_man
    app.jinja_env.filters["new_price_man"] = format_new_price_man
    app.jinja_env.filters["mileage"] = format_mileage
    app.jinja_env.filters["date_kr"] = format_date_kr
    app.jinja_env.filters["fuel_label"] = fuel_label
    app.jinja_env.filters["product_type_label"] = product_type_label
    app.jinja_env.filters["faq_category_label"] = faq_category_label
