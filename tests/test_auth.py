from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import create_app
from app.storage.redis_store import RedisStore
from tests.fakes import FakeRedis


def make_client() -> TestClient:
    app = create_app()
    app.state.store = RedisStore(FakeRedis())
    return TestClient(app)


def restore_settings(snapshot) -> None:
    settings = get_settings()
    for field, value in snapshot.model_dump().items():
        setattr(settings, field, value)


def test_auth_session_reports_disabled_by_default() -> None:
    client = make_client()

    response = client.get("/auth/session")

    assert response.status_code == 200
    assert response.json() == {
        "enabled": False,
        "authenticated": False,
        "username": None,
        "expires_at": None,
        "auth_method": "disabled",
    }


def test_login_creates_cookie_session_and_protects_routes() -> None:
    settings = get_settings()
    original = settings.model_copy(deep=True)
    settings.auth_enabled = True
    settings.auth_admin_username = "admin"
    settings.auth_admin_password = "test-password-2333"
    try:
        client = make_client()

        unauthenticated = client.get("/settings")
        assert unauthenticated.status_code == 401

        login = client.post(
            "/auth/login",
            json={"username": "admin", "password": "test-password-2333"},
        )
        assert login.status_code == 200
        assert login.json()["authenticated"] is True
        assert "proxy_pool_session=" in login.headers["set-cookie"]

        protected = client.get("/settings")
        assert protected.status_code == 200

        logout = client.post("/auth/logout")
        assert logout.status_code == 200
        assert logout.json()["authenticated"] is False

        after_logout = client.get("/settings")
        assert after_logout.status_code == 401
    finally:
        restore_settings(original)


def test_basic_auth_allows_api_access_when_enabled() -> None:
    settings = get_settings()
    original = settings.model_copy(deep=True)
    settings.auth_enabled = True
    settings.auth_admin_username = "admin"
    settings.auth_admin_password = "test-password-2333"
    try:
        client = make_client()

        response = client.get("/stats", auth=("admin", "test-password-2333"))

        assert response.status_code == 200
        assert "total" in response.json()
    finally:
        restore_settings(original)
