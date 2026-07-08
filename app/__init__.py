import os
from pathlib import Path
from flask import Flask, render_template

from app.extensions import db, migrate, login_manager, csrf
from app.utils.filters import register_filters


def create_app(config_class: str | None = None) -> Flask:
    app = Flask(
        __name__,
        instance_path=str(Path(__file__).resolve().parent.parent / "instance"),
        instance_relative_config=True,
    )

    if config_class is None:
        env = os.environ.get("FLASK_ENV", "development")
        config_class = "app.config.ProdConfig" if env == "production" else "app.config.DevConfig"
    app.config.from_object(config_class)

    # Ensure upload directories exist
    Path(app.config["UPLOAD_TMP_DIR"]).mkdir(parents=True, exist_ok=True)
    Path(app.config["UPLOAD_VEHICLES_DIR"]).mkdir(parents=True, exist_ok=True)
    Path(app.config["UPLOAD_BRANDS_DIR"]).mkdir(parents=True, exist_ok=True)
    (Path(app.config["UPLOAD_ROOT"]) / "banners").mkdir(parents=True, exist_ok=True)

    # Extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Ensure models are loaded so Alembic picks them up
    with app.app_context():
        from app import models  # noqa: F401

    # Blueprints
    from app.blueprints.public import public_bp
    from app.blueprints.auth import auth_bp
    from app.blueprints.mypage import mypage_bp
    from app.blueprints.admin import admin_bp
    from app.blueprints.api import api_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(mypage_bp, url_prefix="/mypage")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(api_bp, url_prefix="/api")

    # CLI
    from app.cli import register_cli
    register_cli(app)

    # Jinja filters + globals
    register_filters(app)
    _register_context(app)

    # Error pages
    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template("errors/500.html"), 500

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/403.html"), 403

    return app


def _register_context(app: Flask) -> None:
    from app.services.site_settings import get_kakao_channel_url

    @app.context_processor
    def inject_globals():
        return {
            "kakao_channel_url": get_kakao_channel_url(),
        }
