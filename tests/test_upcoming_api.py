"""Admin upcoming reorder API tests."""
import pytest
from app.extensions import db as _db
from app.models import Brand, UpcomingSlot, Vehicle


@pytest.fixture()
def vehicles(db, brand):
    items = []
    for i in range(4):
        v = Vehicle(
            brand_id=brand.id,
            model=f"M{i}",
            year=2024,
            product_type="subscription",
            visibility="public",
            placement="none",
        )
        db.session.add(v)
        items.append(v)
    db.session.commit()
    return items


def test_get_empty_order(admin_client, db):
    res = admin_client.get("/admin/api/upcoming/order")
    assert res.status_code == 200
    assert res.get_json() == {"group_a": [], "group_b": []}


def test_patch_reorder(admin_client, vehicles, db):
    ids = [v.id for v in vehicles]
    res = admin_client.patch(
        "/admin/api/upcoming/order",
        json={"group_a": ids[:2], "group_b": ids[2:]},
    )
    assert res.status_code == 200
    assert res.get_json() == {"ok": True}

    order = admin_client.get("/admin/api/upcoming/order").get_json()
    assert order["group_a"] == ids[:2]
    assert order["group_b"] == ids[2:]
    assert UpcomingSlot.query.count() == 4


def test_patch_reject_duplicate(admin_client, vehicles, db):
    ids = [v.id for v in vehicles]
    res = admin_client.patch(
        "/admin/api/upcoming/order",
        json={"group_a": [ids[0], ids[0]], "group_b": []},
    )
    assert res.status_code == 400


def test_patch_reject_unknown_vehicle(admin_client, vehicles, db):
    res = admin_client.patch(
        "/admin/api/upcoming/order",
        json={"group_a": [99999], "group_b": []},
    )
    assert res.status_code == 400


def test_patch_reject_overlap_between_groups(admin_client, vehicles, db):
    ids = [v.id for v in vehicles]
    res = admin_client.patch(
        "/admin/api/upcoming/order",
        json={"group_a": [ids[0]], "group_b": [ids[0]]},
    )
    assert res.status_code == 400


def test_add_to_group(admin_client, vehicles, db):
    res = admin_client.post(
        "/admin/api/upcoming/add",
        json={"vehicle_id": vehicles[0].id, "group": "a"},
    )
    assert res.status_code == 200
    assert UpcomingSlot.query.filter_by(vehicle_id=vehicles[0].id, group="a").first()


def test_remove_from_upcoming(admin_client, vehicles, db):
    admin_client.post(
        "/admin/api/upcoming/add",
        json={"vehicle_id": vehicles[0].id, "group": "a"},
    )
    res = admin_client.delete(f"/admin/api/upcoming/{vehicles[0].id}")
    assert res.status_code == 200
    assert UpcomingSlot.query.count() == 0


def test_regular_user_cannot_patch(user_client, vehicles, db):
    res = user_client.patch(
        "/admin/api/upcoming/order",
        json={"group_a": [], "group_b": []},
    )
    assert res.status_code == 403
    assert UpcomingSlot.query.count() == 0
