"""Public-side smoke tests."""
from app.models import Vehicle


def _seed_vehicles(db, brand, n=14):
    for i in range(n):
        db.session.add(Vehicle(
            brand_id=brand.id,
            model=f"M{i}",
            year=2024,
            product_type="subscription",
            visibility="public",
            placement="collection",
            price_min_man=100 + i,
        ))
    db.session.commit()


def test_home_200(client, brand, db):
    _seed_vehicles(db, brand, n=4)
    res = client.get("/")
    assert res.status_code == 200


def test_catalog_pagination(client, brand, db):
    _seed_vehicles(db, brand, n=14)
    p1 = client.get("/vehicles?page=1")
    p2 = client.get("/vehicles?page=2")
    assert p1.status_code == 200
    assert p2.status_code == 200
    assert p1.data.count(b'class="v-card') == 12
    assert p2.data.count(b'class="v-card') == 2


def test_catalog_brand_filter(client, brand, db):
    _seed_vehicles(db, brand, n=3)
    res = client.get("/vehicles?brand=bmw")
    assert res.status_code == 200
    assert res.data.count(b'class="v-card') == 3


def test_upcoming_200(client, db):
    res = client.get("/upcoming")
    assert res.status_code == 200


def test_faq_200(client, db):
    res = client.get("/faq")
    assert res.status_code == 200
