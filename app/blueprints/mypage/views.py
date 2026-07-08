from flask import render_template
from flask_login import current_user, login_required

from app.models import Favorite, Vehicle
from . import mypage_bp


@mypage_bp.route("/")
@login_required
def index():
    favs = (
        Vehicle.query.join(Favorite, Favorite.vehicle_id == Vehicle.id)
        .filter(Favorite.user_id == current_user.id)
        .order_by(Favorite.created_at.desc())
        .all()
    )
    return render_template("mypage/index.html", favorites=favs)
