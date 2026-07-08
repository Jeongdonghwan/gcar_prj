from datetime import datetime
from app.extensions import db


FAQ_CATEGORIES = ("signup", "vehicle", "subscription", "insurance", "inspection", "return", "etc")


class Banner(db.Model):
    """Hero banner shown on the home page. Multiple visible rows auto-rotate."""
    __tablename__ = "banner"

    id = db.Column(db.Integer, primary_key=True)
    eyebrow = db.Column(db.String(60))           # e.g. "FOR SUBSCRIBERS"
    title = db.Column(db.String(120), nullable=False)
    subtitle = db.Column(db.String(200))
    link_url = db.Column(db.String(255))         # optional click-through
    image_path = db.Column(db.String(255))       # background image URL/path (e.g. /static/img/hero/1.png)
    sort_order = db.Column(db.Integer, default=0, nullable=False)
    is_visible = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class Notice(db.Model):
    __tablename__ = "notice"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)  # Markdown source
    is_pinned = db.Column(db.Boolean, default=False, nullable=False)
    is_visible = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class FAQ(db.Model):
    __tablename__ = "faq"

    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.Enum(*FAQ_CATEGORIES, name="faq_category"), nullable=False)
    question = db.Column(db.String(300), nullable=False)
    answer = db.Column(db.Text, nullable=False)
    sort_order = db.Column(db.Integer, default=0, nullable=False)
    is_visible = db.Column(db.Boolean, default=True, nullable=False)
