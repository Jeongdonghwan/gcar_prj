from flask import Blueprint, abort, request
from flask_login import current_user

admin_bp = Blueprint("admin", __name__, template_folder="../../templates")


@admin_bp.before_request
def _guard():
    # /admin/login is reached via /auth/login; admin guard applies to all admin routes
    if not current_user.is_authenticated:
        from flask import redirect, url_for
        return redirect(url_for("auth.login", next=request.path))
    if not getattr(current_user, "is_admin", False):
        abort(403)


from . import views  # noqa: E402,F401
from . import api_views  # noqa: E402,F401
