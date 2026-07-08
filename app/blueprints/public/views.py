from flask import abort, render_template, request
from sqlalchemy import asc, desc

from app.extensions import db
from app.models import Banner, Brand, FAQ, Notice, UpcomingSlot, Vehicle
from app.models.content import FAQ_CATEGORIES
from . import public_bp


def _public_vehicles_query():
    return Vehicle.query.filter(Vehicle.visibility.in_(("public", "soldout")))


@public_bp.route("/")
def index():
    brands = (
        Brand.query.filter_by(is_visible=True).order_by(Brand.sort_order.asc()).all()
    )
    banners = (
        Banner.query.filter_by(is_visible=True)
        .order_by(Banner.sort_order.asc(), Banner.id.asc())
        .all()
    )
    q = (
        _public_vehicles_query()
        .filter(Vehicle.placement == "collection")
        .order_by(desc(Vehicle.is_featured), desc(Vehicle.created_at))
    )
    vehicles = q.limit(40).all()
    return render_template(
        "public/index.html",
        vehicles=vehicles, brands=brands, banners=banners,
    )


@public_bp.route("/vehicles")
def vehicles_list():
    brands = (
        Brand.query.filter_by(is_visible=True).order_by(Brand.sort_order.asc()).all()
    )
    sort = request.args.get("sort", "recommended")
    brand_slug = request.args.get("brand")
    page = max(int(request.args.get("page", 1) or 1), 1)

    q = _public_vehicles_query()
    if brand_slug:
        q = q.join(Brand).filter(Brand.slug == brand_slug)

    if sort == "price_asc":
        q = q.order_by(asc(Vehicle.price_min_man))
    elif sort == "price_desc":
        q = q.order_by(desc(Vehicle.price_min_man))
    elif sort == "newest":
        q = q.order_by(desc(Vehicle.created_at))
    else:
        q = q.order_by(desc(Vehicle.is_featured), desc(Vehicle.created_at))

    pagination = q.paginate(page=page, per_page=12, error_out=False)
    return render_template(
        "public/vehicles_list.html",
        pagination=pagination,
        brands=brands,
        active_brand=brand_slug,
        active_sort=sort,
    )


@public_bp.route("/vehicles/<int:vehicle_id>")
def vehicle_detail(vehicle_id: int):
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    if vehicle.visibility == "hidden":
        abort(404)
    related = (
        _public_vehicles_query()
        .filter(Vehicle.id != vehicle.id, Vehicle.brand_id == vehicle.brand_id)
        .order_by(desc(Vehicle.is_featured))
        .limit(4)
        .all()
    )
    return render_template(
        "public/vehicle_detail.html", vehicle=vehicle, related=related
    )


@public_bp.route("/upcoming")
def upcoming():
    slots = (
        db.session.query(UpcomingSlot, Vehicle)
        .join(Vehicle, Vehicle.id == UpcomingSlot.vehicle_id)
        .filter(Vehicle.visibility != "hidden")
        .order_by(UpcomingSlot.group.asc(), UpcomingSlot.position.asc())
        .all()
    )
    group_a = [v for s, v in slots if s.group == "a"]
    group_b = [v for s, v in slots if s.group == "b"]
    return render_template(
        "public/upcoming.html", group_a=group_a, group_b=group_b
    )


@public_bp.route("/faq")
def faq():
    category = request.args.get("category")
    q = FAQ.query.filter_by(is_visible=True)
    if category and category in FAQ_CATEGORIES:
        q = q.filter_by(category=category)
    faqs = q.order_by(FAQ.sort_order.asc(), FAQ.id.asc()).all()
    notices = (
        Notice.query.filter_by(is_visible=True)
        .order_by(Notice.is_pinned.desc(), Notice.created_at.desc())
        .limit(5)
        .all()
    )
    return render_template(
        "public/faq.html",
        faqs=faqs,
        notices=notices,
        categories=FAQ_CATEGORIES,
        active_category=category,
    )


@public_bp.route("/notices")
def notices():
    items = (
        Notice.query.filter_by(is_visible=True)
        .order_by(Notice.is_pinned.desc(), Notice.created_at.desc())
        .all()
    )
    return render_template("public/notices.html", notices=items)


@public_bp.route("/notices/<int:notice_id>")
def notice_detail(notice_id: int):
    notice = Notice.query.get_or_404(notice_id)
    if not notice.is_visible:
        abort(404)
    return render_template("public/notice_detail.html", notice=notice)


@public_bp.route("/terms/<which>")
def terms(which: str):
    if which not in ("service", "privacy"):
        abort(404)
    return render_template(f"public/terms_{which}.html")
