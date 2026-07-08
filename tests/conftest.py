"""pytest fixtures for GA:RAGE.

Uses a file-based SQLite DB per session for portability and to avoid the
in-memory ":memory:" connection-isolation pitfall with Flask-SQLAlchemy.
"""
import os
from pathlib import Path
import pytest

from app import create_app
from app.extensions import db as _db
from app.models import Brand, User


@pytest.fixture(scope="session")
def app(tmp_path_factory):
    db_file = tmp_path_factory.mktemp("db") / "test.sqlite"
    upload_dir = tmp_path_factory.mktemp("uploads")
    (upload_dir / "_tmp").mkdir()
    (upload_dir / "vehicles").mkdir()

    # Override env so BaseConfig DB URI is replaced
    os.environ["SECRET_KEY"] = "test-secret-key"
    app = create_app("app.config.TestConfig")
    app.config.update(
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{db_file.as_posix()}",
        SQLALCHEMY_ENGINE_OPTIONS={},
        UPLOAD_ROOT=upload_dir,
        UPLOAD_TMP_DIR=upload_dir / "_tmp",
        UPLOAD_VEHICLES_DIR=upload_dir / "vehicles",
        WTF_CSRF_ENABLED=False,
        SERVER_NAME="localhost",
    )

    with app.app_context():
        _db.create_all()
        yield app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture()
def db(app):
    """Per-test transactional rollback. Each test starts with empty data."""
    with app.app_context():
        # Truncate tables instead of drop/create (faster)
        for table in reversed(_db.metadata.sorted_tables):
            _db.session.execute(table.delete())
        _db.session.commit()
        yield _db


@pytest.fixture()
def client(app, db):
    return app.test_client()


@pytest.fixture()
def admin_user(db):
    u = User(email="admin@test.dev", name="Admin", is_admin=True)
    u.set_password("admin-pw")
    db.session.add(u)
    db.session.commit()
    return u


@pytest.fixture()
def regular_user(db):
    u = User(email="user@test.dev", name="User")
    u.set_password("user-pw")
    db.session.add(u)
    db.session.commit()
    return u


@pytest.fixture()
def brand(db):
    b = Brand(name="BMW", slug="bmw", sort_order=0)
    db.session.add(b)
    db.session.commit()
    return b


@pytest.fixture()
def login_as(client):
    """Login helper. Usage: login_as(admin_user)."""
    def _login(user, password):
        return client.post(
            "/auth/login",
            data={"email": user.email, "password": password},
            follow_redirects=False,
        )
    return _login


@pytest.fixture()
def admin_client(client, admin_user, login_as):
    login_as(admin_user, "admin-pw")
    return client


@pytest.fixture()
def user_client(client, regular_user, login_as):
    login_as(regular_user, "user-pw")
    return client
