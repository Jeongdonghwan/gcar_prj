from flask import current_app, jsonify, request

from app.extensions import db
from app.models import Brand, Vehicle, VehicleImage
from app.services import image_service, upcoming_service
from . import admin_bp


# --- Upcoming order API ----------------------------------------------------
@admin_bp.route("/api/upcoming/order", methods=["GET"])
def api_get_upcoming_order():
    return jsonify(upcoming_service.get_order())


@admin_bp.route("/api/upcoming/order", methods=["PATCH"])
def api_patch_upcoming_order():
    data = request.get_json(silent=True) or {}
    try:
        upcoming_service.reorder(
            list(data.get("group_a") or []),
            list(data.get("group_b") or []),
        )
    except upcoming_service.UpcomingPayloadError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify({"ok": True})


@admin_bp.route("/api/upcoming/add", methods=["POST"])
def api_add_upcoming():
    data = request.get_json(silent=True) or {}
    try:
        upcoming_service.add_to_group(int(data["vehicle_id"]), data.get("group", "a"))
    except (KeyError, ValueError, upcoming_service.UpcomingPayloadError) as e:
        return jsonify({"error": str(e)}), 400
    return jsonify({"ok": True})


@admin_bp.route("/api/upcoming/<int:vehicle_id>", methods=["DELETE"])
def api_remove_upcoming(vehicle_id: int):
    upcoming_service.remove(vehicle_id)
    return jsonify({"ok": True})


# --- Brand logo API -------------------------------------------------------
@admin_bp.route("/api/brands/<int:brand_id>/logo", methods=["POST"])
def api_upload_brand_logo(brand_id: int):
    brand = Brand.query.get_or_404(brand_id)
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "file 필드가 필요합니다."}), 400
    try:
        rel_path = image_service.upload_for_brand(brand.id, file)
    except image_service.ImageError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify({"logo_path": rel_path})


# --- Banner image API -----------------------------------------------------
@admin_bp.route("/api/banners/<int:banner_id>/image", methods=["POST"])
def api_upload_banner_image(banner_id: int):
    from app.models import Banner
    banner = Banner.query.get_or_404(banner_id)
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "file 필드가 필요합니다."}), 400
    try:
        rel_path = image_service.upload_for_banner(banner.id, file)
    except image_service.ImageError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify({"image_path": rel_path})


# --- Vehicle images API ----------------------------------------------------
@admin_bp.route("/api/vehicles/<int:vehicle_id>/images", methods=["POST"])
def api_upload_image(vehicle_id: int):
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    files = request.files.getlist("file")
    if not files:
        return jsonify({"error": "file 필드가 필요합니다."}), 400
    try:
        results = [image_service.upload_for_vehicle(vehicle.id, f) for f in files]
    except image_service.ImageError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify({
        "images": [
            {
                "id": img.id,
                "path": img.file_path,
                "is_primary": img.is_primary,
                "sort_order": img.sort_order,
            }
            for img in results
        ]
    })


@admin_bp.route("/api/vehicles/<int:vehicle_id>/images/order", methods=["PATCH"])
def api_reorder_images(vehicle_id: int):
    Vehicle.query.get_or_404(vehicle_id)
    data = request.get_json(silent=True) or {}
    ids = data.get("ids") or []
    if not isinstance(ids, list):
        return jsonify({"error": "ids must be a list"}), 400
    image_service.reorder_images(vehicle_id, [int(x) for x in ids])
    return jsonify({"ok": True})


@admin_bp.route("/api/vehicles/<int:vehicle_id>/images/<int:image_id>/primary", methods=["POST"])
def api_set_primary(vehicle_id: int, image_id: int):
    image_service.set_primary(image_id)
    return jsonify({"ok": True})


@admin_bp.route("/api/vehicles/<int:vehicle_id>/images/<int:image_id>", methods=["DELETE"])
def api_delete_image(vehicle_id: int, image_id: int):
    image_service.delete_image(image_id)
    return jsonify({"ok": True})
