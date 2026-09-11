"""Q&A(1:1 문의) 게시판 + 고객센터 설정."""
from app.models import QnaPost


def _make_post(db, user, title="문의합니다", private=True):
    p = QnaPost(user_id=user.id, title=title, body="내용", is_private=private)
    db.session.add(p)
    db.session.commit()
    return p


class TestQnaPublic:
    def test_list_page_renders(self, client):
        res = client.get("/qna")
        assert res.status_code == 200
        assert "1:1 문의" in res.get_data(as_text=True)

    def test_write_requires_login(self, client):
        res = client.get("/qna/write")
        assert res.status_code == 302
        assert "/auth/login" in res.headers["Location"]

    def test_member_can_write(self, user_client, regular_user, db):
        res = user_client.post(
            "/qna/write",
            data={"title": "구독 문의", "body": "3개월 가격이 궁금해요", "is_private": "y"},
            follow_redirects=False,
        )
        assert res.status_code == 302
        post = QnaPost.query.one()
        assert post.user_id == regular_user.id
        assert post.is_private is True

    def test_private_post_hidden_from_others(self, client, db, admin_user):
        post = _make_post(db, admin_user, private=True)
        res = client.get(f"/qna/{post.id}")
        assert res.status_code == 302  # anonymous → login

    def test_private_post_visible_to_author(self, user_client, regular_user, db):
        post = _make_post(db, regular_user, private=True)
        res = user_client.get(f"/qna/{post.id}")
        assert res.status_code == 200
        assert "문의합니다" in res.get_data(as_text=True)

    def test_private_title_masked_in_list(self, client, db, admin_user):
        _make_post(db, admin_user, title="비밀 제목", private=True)
        html = client.get("/qna").get_data(as_text=True)
        assert "비밀 제목" not in html
        assert "비밀글" in html

    def test_public_post_visible_to_anyone(self, client, db, admin_user):
        post = _make_post(db, admin_user, private=False)
        res = client.get(f"/qna/{post.id}")
        assert res.status_code == 200


class TestQnaAdmin:
    def test_admin_can_answer(self, admin_client, regular_user, db):
        post = _make_post(db, regular_user)
        res = admin_client.post(
            f"/admin/qna/{post.id}", data={"answer": "안내드립니다."}, follow_redirects=False
        )
        assert res.status_code == 302
        db.session.refresh(post)
        assert post.is_answered
        assert post.answered_at is not None

    def test_regular_user_blocked_from_admin_qna(self, user_client, regular_user, db):
        post = _make_post(db, regular_user)
        assert user_client.get(f"/admin/qna/{post.id}").status_code == 403


class TestContactSettings:
    def test_footer_shows_default_phone(self, client):
        html = client.get("/").get_data(as_text=True)
        assert "000-0000-0000" in html

    def test_admin_can_change_phone(self, admin_client, client):
        res = admin_client.post(
            "/admin/settings",
            data={"contact_phone": "010-1234-5678", "contact_hours": "24시간 상담 가능"},
            follow_redirects=False,
        )
        assert res.status_code == 302
        html = client.get("/").get_data(as_text=True)
        assert "010-1234-5678" in html
