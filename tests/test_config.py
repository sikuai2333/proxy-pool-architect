import pytest

from app.core.config import Settings


def test_settings_parse_csv_string_lists() -> None:
    settings = Settings(
        cors_allowed_origins="https://dashboard.example.com, https://admin.example.com",
        allowed_hosts="dashboard.example.com,api.example.com",
    )

    assert settings.cors_allowed_origins == [
        "https://dashboard.example.com",
        "https://admin.example.com",
    ]
    assert settings.allowed_hosts == [
        "dashboard.example.com",
        "api.example.com",
    ]


def test_settings_keep_json_list_env_inputs(monkeypatch) -> None:
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", '["https://dashboard.example.com"]')
    monkeypatch.setenv("ALLOWED_HOSTS", '["dashboard.example.com", "api.example.com"]')
    settings = Settings(_env_file=None)

    assert settings.cors_allowed_origins == ["https://dashboard.example.com"]
    assert settings.allowed_hosts == ["dashboard.example.com", "api.example.com"]


def test_settings_parse_csv_env_inputs(monkeypatch) -> None:
    monkeypatch.setenv(
        "CORS_ALLOWED_ORIGINS",
        "https://dashboard.example.com, https://admin.example.com",
    )
    monkeypatch.setenv("ALLOWED_HOSTS", "dashboard.example.com,api.example.com")
    settings = Settings(_env_file=None)

    assert settings.cors_allowed_origins == [
        "https://dashboard.example.com",
        "https://admin.example.com",
    ]
    assert settings.allowed_hosts == [
        "dashboard.example.com",
        "api.example.com",
    ]


def test_settings_require_admin_credentials_when_auth_enabled() -> None:
    with pytest.raises(
        ValueError,
        match="AUTH_ENABLED requires both AUTH_ADMIN_USERNAME and AUTH_ADMIN_PASSWORD",
    ):
        Settings(auth_enabled=True, auth_admin_username="admin", auth_admin_password="")
