"""Admin vehicle registration / edit / delete (TDD)."""
import pytest
from app.models import Vehicle, UpcomingSlot


def _form_data(brand_id, **overrides):
    base = {
        "brand_id": str(brand_id),
        "model": "5 Series 530i M Sport",
        "year": "2024",
        "color": "그라파이트",
        "mileage_km": "10",
        "fuel": "gasoline",
        "transmission": "auto",
        "price_min_man": "239",
        "price_max_man": "265",
        "product_type": "subscription",
        "visibility": "public",
        "upcoming_group": "none",
        "show_in_collection": "y",
        "headline": "수리비 무제한",
        "description": "본문",
        "options": ["ventilated_seat", "hud"],
    }
    base.update({k: ("" if v is None else str(v)) for k, v in overrides.items()})
    return base


def test_get_new_form(admin_client, brand):
    res = admin_client.get("/admin/vehicles/new")
    assert res.status_code == 200
    # Brand dropdown rendered with seeded option
    assert b'value="' + str(brand.id).encode() + b'"' in res.data


def test_create_vehicle(admin_client, brand, db):
    res = admin_client.post(
        "/admin/vehicles/new",
        data=_form_data(brand.id),
        follow_redirects=False,
    )
    assert res.status_code == 302, res.data
    v = Vehicle.query.first()
    assert v is not None
    assert v.model == "5 Series 530i M Sport"
    assert v.brand_id == brand.id
    assert v.price_min_man == 239
    assert v.placement == "collection"
    assert v.product_type == "subscription"
    assert v.options_json == ["ventilated_seat", "hud"]


def test_create_vehicle_invalid_missing_model(admin_client, brand, db):
    data = _form_data(brand.id)
    data["model"] = ""
    res = admin_client.post("/admin/vehicles/new", data=data, follow_redirects=False)
    # Form re-renders on invalid (no redirect)
    assert res.status_code == 200
    assert Vehicle.query.count() == 0


def test_create_vehicle_with_upcoming_group_a(admin_client, brand, db):
    data = _form_data(brand.id)
    data["show_in_collection"] = ""
    data["upcoming_group"] = "a"
    res = admin_client.post("/admin/vehicles/new", data=data, follow_redirects=False)
    assert res.status_code == 302
    v = Vehicle.query.first()
    assert v is not None
    assert v.placement == "none"
    slot = UpcomingSlot.query.filter_by(vehicle_id=v.id).first()
    assert slot is not None
    assert slot.group == "a"


def test_edit_vehicle(admin_client, brand, db):
    admin_client.post("/admin/vehicles/new", data=_form_data(brand.id))
    v = Vehicle.query.first()
    res = admin_client.post(
        f"/admin/vehicles/{v.id}/edit",
        data=_form_data(brand.id, model="X5 xDrive40i", price_min_man=339),
        follow_redirects=False,
    )
    assert res.status_code == 302
    db.session.refresh(v)
    assert v.model == "X5 xDrive40i"
    assert v.price_min_man == 339


def test_delete_vehicle(admin_client, brand, db):
    admin_client.post("/admin/vehicles/new", data=_form_data(brand.id))
    v = Vehicle.query.first()
    res = admin_client.post(f"/admin/vehicles/{v.id}/delete", follow_redirects=False)
    assert res.status_code == 302
    assert Vehicle.query.count() == 0


def test_list_vehicles(admin_client, brand, db):
    for i in range(3):
        admin_client.post("/admin/vehicles/new", data=_form_data(brand.id, model=f"Model {i}"))
    res = admin_client.get("/admin/vehicles")
    assert res.status_code == 200
    assert res.data.count(b"Model 0") >= 1
    assert res.data.count(b"Model 1") >= 1
    assert res.data.count(b"Model 2") >= 1


def test_regular_user_cannot_create(user_client, brand, db):
    res = user_client.post("/admin/vehicles/new", data=_form_data(brand.id), follow_redirects=False)
    assert res.status_code == 403
    assert Vehicle.query.count() == 0
