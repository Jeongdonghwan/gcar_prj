"""Admin banner CRUD tests."""
from app.models import Banner


def _form(**overrides):
    base = {
        "eyebrow": "FOR SUBSCRIBERS",
        "title": "수리비 0원",
        "subtitle": "보증수리 무제한",
        "link_url": "",
        "sort_order": "0",
        "is_visible": "y",
    }
    base.update({k: ("" if v is None else str(v)) for k, v in overrides.items()})
    return base


def test_banner_list_empty(admin_client):
    res = admin_client.get("/admin/banners")
    assert res.status_code == 200
    assert "등록된 배너가 없습니다".encode("utf-8") in res.data


def test_create_banner(admin_client, db):
    res = admin_client.post("/admin/banners/new", data=_form(), follow_redirects=False)
    assert res.status_code == 302
    b = Banner.query.first()
    assert b is not None
    assert b.title == "수리비 0원"
    assert b.is_visible is True


def test_create_banner_without_title_defaults(admin_client, db):
    """Banner is now image-first — title is optional in form; server defaults to '배너'."""
    res = admin_client.post("/admin/banners/new", data=_form(title=""), follow_redirects=False)
    assert res.status_code == 302
    b = Banner.query.first()
    assert b is not None
    assert b.title == "배너"


def test_edit_banner(admin_client, db):
    admin_client.post("/admin/banners/new", data=_form())
    b = Banner.query.first()
    res = admin_client.post(
        f"/admin/banners/{b.id}/edit",
        data=_form(title="새 캠페인", sort_order="5"),
        follow_redirects=False,
    )
    assert res.status_code == 302
    db.session.refresh(b)
    assert b.title == "새 캠페인"
    assert b.sort_order == 5


def test_delete_banner(admin_client, db):
    admin_client.post("/admin/banners/new", data=_form())
    b = Banner.query.first()
    res = admin_client.post(f"/admin/banners/{b.id}/delete", follow_redirects=False)
    assert res.status_code == 302
    assert Banner.query.count() == 0


def test_banner_appears_on_home(client, admin_client, brand, db):
    admin_client.post("/admin/banners/new", data=_form(title="홈에서 보일 캠페인"))
    # Logout the admin session to test public render
    client.get("/auth/logout")
    res = client.get("/")
    assert res.status_code == 200
    assert "홈에서 보일 캠페인".encode("utf-8") in res.data


def test_hidden_banner_not_on_home(client, admin_client, brand, db):
    admin_client.post("/admin/banners/new", data=_form(title="숨김 배너", is_visible=""))
    client.get("/auth/logout")
    res = client.get("/")
    assert res.status_code == 200
    assert "숨김 배너".encode("utf-8") not in res.data


def test_regular_user_cannot_create_banner(user_client, db):
    res = user_client.post("/admin/banners/new", data=_form(), follow_redirects=False)
    assert res.status_code == 403
    assert Banner.query.count() == 0
