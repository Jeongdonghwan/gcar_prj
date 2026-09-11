from datetime import datetime
from app.extensions import db


class Favorite(db.Model):
    __tablename__ = "favorite"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    vehicle_id = db.Column(
        db.Integer, db.ForeignKey("vehicle.id", ondelete="CASCADE"), nullable=False
    )
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (db.UniqueConstraint("user_id", "vehicle_id", name="uq_user_vehicle_fav"),)


class Inquiry(db.Model):
    __tablename__ = "inquiry"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey("vehicle.id"), nullable=True)
    source = db.Column(db.String(40))   # detail_cta / floating / faq / upcoming
    user_agent = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class QnaPost(db.Model):
    """고객센터 1:1 문의 게시판. 회원만 작성, 비공개 글은 작성자·관리자만 열람."""
    __tablename__ = "qna_post"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    is_private = db.Column(db.Boolean, default=True, nullable=False)

    answer = db.Column(db.Text)
    answered_at = db.Column(db.DateTime)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship("User", backref=db.backref("qna_posts", lazy="dynamic"))

    @property
    def is_answered(self) -> bool:
        return bool(self.answer)

    def can_view(self, user) -> bool:
        if not self.is_private:
            return True
        if not getattr(user, "is_authenticated", False):
            return False
        return user.id == self.user_id or getattr(user, "is_admin", False)


class SiteSetting(db.Model):
    __tablename__ = "site_setting"

    key = db.Column(db.String(60), primary_key=True)
    value = db.Column(db.Text)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
