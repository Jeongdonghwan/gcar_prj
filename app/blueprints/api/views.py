from flask import jsonify, request
from flask_login import current_user, login_required

from app.extensions import db
from app.models import Brand, FAQ, Favorite, Inquiry, Notice, UpcomingSlot, Vehicle
from app.models.content import FAQ_CATEGORIES
from . import api_bp


@api_bp.route("/vehicles")
def list_vehicles():
    type_filter = request.args.get("type", "all")
    brand_slug = request.args.get("brand")
    sort = request.args.get("sort", "recommended")

    q = Vehicle.query.filter(
        Vehicle.visibility.in_(("public", "soldout")),
        Vehicle.placement == "collection",
    )
    if type_filter in ("subscription", "rent", "super"):
        q = q.filter(Vehicle.product_type == type_filter)
    if brand_slug:
        q = q.join(Brand).filter(Brand.slug == brand_slug)
    if sort == "price_asc":
        q = q.order_by(Vehicle.price_min_man.asc())
    elif sort == "price_desc":
        q = q.order_by(Vehicle.price_min_man.desc())
    elif sort == "newest":
        q = q.order_by(Vehicle.created_at.desc())
    else:
        q = q.order_by(Vehicle.is_featured.desc(), Vehicle.created_at.desc())

    return jsonify([_vehicle_dict(v) for v in q.limit(50).all()])


@api_bp.route("/vehicles/<int:vehicle_id>")
def vehicle_detail(vehicle_id: int):
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    return jsonify(_vehicle_dict(vehicle, full=True))


@api_bp.route("/upcoming")
def upcoming():
    slots = (
        db.session.query(UpcomingSlot, Vehicle)
        .join(Vehicle, Vehicle.id == UpcomingSlot.vehicle_id)
        .filter(Vehicle.visibility != "hidden")
        .order_by(UpcomingSlot.group.asc(), UpcomingSlot.position.asc())
        .all()
    )
    return jsonify({
        "group_a": [_vehicle_dict(v) for s, v in slots if s.group == "a"],
        "group_b": [_vehicle_dict(v) for s, v in slots if s.group == "b"],
    })


@api_bp.route("/faq")
def faq_list():
    category = request.args.get("category")
    q = FAQ.query.filter_by(is_visible=True)
    if category and category in FAQ_CATEGORIES:
        q = q.filter_by(category=category)
    return jsonify([
        {"id": f.id, "category": f.category, "question": f.question, "answer": f.answer}
        for f in q.order_by(FAQ.sort_order.asc()).all()
    ])


@api_bp.route("/notices")
def notice_list():
    items = (
        Notice.query.filter_by(is_visible=True)
        .order_by(Notice.is_pinned.desc(), Notice.created_at.desc())
        .all()
    )
    return jsonify([
        {
            "id": n.id,
            "title": n.title,
            "is_pinned": n.is_pinned,
            "created_at": n.created_at.isoformat(),
        }
        for n in items
    ])


@api_bp.route("/favorites/<int:vehicle_id>", methods=["POST"])
@login_required
def toggle_favorite(vehicle_id: int):
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    existing = Favorite.query.filter_by(
        user_id=current_user.id, vehicle_id=vehicle.id
    ).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
        return jsonify({"favored": False})
    fav = Favorite(user_id=current_user.id, vehicle_id=vehicle.id)
    db.session.add(fav)
    db.session.commit()
    return jsonify({"favored": True})


@api_bp.route("/inquiries", methods=["POST"])
def log_inquiry():
    data = request.get_json(silent=True) or {}
    source = data.get("source", "unknown")[:40]
    vehicle_id = data.get("vehicle_id")
    inq = Inquiry(
        user_id=current_user.id if current_user.is_authenticated else None,
        vehicle_id=int(vehicle_id) if vehicle_id else None,
        source=source,
        user_agent=(request.headers.get("User-Agent") or "")[:255],
    )
    db.session.add(inq)
    db.session.commit()
    return jsonify({"ok": True})


def _vehicle_dict(v: Vehicle, full: bool = False) -> dict:
    primary = v.primary_image
    base = {
        "id": v.id,
        "brand": v.brand_name,
        "model": v.model,
        "trim": v.trim,
        "year": v.year,
        "price_min_man": v.price_min_man,
        "price_max_man": v.price_max_man,
        "new_price_man": v.new_price_man,
        "product_type": v.product_type,
        "visibility": v.visibility,
        "is_featured": v.is_featured,
        "is_fast": v.is_fast,
        "is_deal": v.is_deal,
        "eta_label": v.eta_label,
        "primary_image": primary.file_path if primary else None,
    }
    if full:
        base.update({
            "headline": v.headline,
            "description": v.description,
            "color": v.color,
            "fuel": v.fuel,
            "transmission": v.transmission,
            "mileage_km": v.mileage_km,
            "options": v.options_json or [],
            "images": [
                {"path": i.file_path, "is_primary": i.is_primary, "sort_order": i.sort_order}
                for i in v.images
            ],
        })
    return base
