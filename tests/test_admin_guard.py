"""Auth/permission guard tests for /admin/*."""


def test_anonymous_redirected_to_login(client):
    res = client.get("/admin/", follow_redirects=False)
    assert res.status_code == 302
    assert "/auth/login" in res.headers["Location"]


def test_regular_user_gets_403(user_client):
    res = user_client.get("/admin/", follow_redirects=False)
    assert res.status_code == 403


def test_admin_reaches_dashboard(admin_client):
    res = admin_client.get("/admin/", follow_redirects=False)
    assert res.status_code == 200
    assert "대시보드".encode("utf-8") in res.data
