import json
from functools import lru_cache
from typing import Annotated, Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "ProxyPool Architect"
    app_version: str = "0.1.0"
    app_env: str = "dev"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    auth_enabled: bool = False
    auth_admin_username: str = ""
    auth_admin_password: str = ""
    auth_session_ttl_seconds: int = Field(default=43200, ge=60)
    auth_session_cookie_name: str = "proxy_pool_session"
    auth_session_secure: bool = False
    auth_session_samesite: Literal["lax", "strict", "none"] = "lax"
    cors_allowed_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["http://localhost:5173", "http://127.0.0.1:5173"]
    )
    cors_allow_credentials: bool = False
    allowed_hosts: Annotated[list[str], NoDecode] = Field(default_factory=list)
    gzip_minimum_size: int = Field(default=1024, ge=0)
    log_level: str = "INFO"
    log_json: bool = False
    db_path: str = "data/proxy_pool.db"

    provider_static_enabled: bool = True
    provider_static_proxies: list[str] = Field(default_factory=list)
    provider_url_lists_enabled: bool = False
    provider_url_list_urls: list[str] = Field(default_factory=list)
    provider_url_timeout_seconds: float = Field(default=10.0, gt=0)
    provider_url_concurrency: int = Field(default=5, ge=1)
    provider_config_file: str = "config/providers.yaml"
    provider_plugin_allowed_prefixes: list[str] = Field(default_factory=lambda: ["app.providers."])
    github_mirrors: list[str] = Field(default_factory=list)

    geo_enabled: bool = False
    geo_file: str = "config/geo.csv"

    validate_concurrency: int = Field(default=100, ge=1)
    validate_timeout_seconds: float = Field(default=10.0, gt=0)
    test_url: str = "https://httpbin.org/ip"
    anonymity_test_url: str = "https://httpbin.org/headers"
    validator_original_ip: str | None = None
    min_elite_score: int = 80
    cooldown_seconds: int = Field(default=1800, ge=1)
    session_affinity_ttl_seconds: int = Field(default=3600, ge=1)

    gateway_enabled: bool = False
    gateway_port: int = 7890
    gateway_host: str = "127.0.0.1"
    gateway_default_country: str | None = None
    gateway_default_scheme: str | None = None
    gateway_default_strategy: str = "best"

    scheduler_enabled: bool = False
    fetch_interval_seconds: int = Field(default=1800, ge=1)
    validate_interval_seconds: int = Field(default=600, ge=1)
    validate_batch_size: int = Field(default=100, ge=1)
    metrics_enabled: bool = True
    safe_authorized_targets_only: bool = True
    safe_block_private_networks: bool = True
    safe_mask_proxy_credentials: bool = True
    runtime_event_limit: int = Field(default=500, ge=1)
    runtime_validation_job_limit: int = Field(default=200, ge=1)
    runtime_event_retention_seconds: int = Field(default=86400, ge=1)
    runtime_validation_job_retention_seconds: int = Field(default=604800, ge=1)

    @model_validator(mode="before")
    @classmethod
    def _parse_list_fields(cls, values: object) -> object:
        if not isinstance(values, dict):
            return values

        for field_name in ("cors_allowed_origins", "allowed_hosts", "github_mirrors"):
            value = values.get(field_name)
            if value is None or isinstance(value, list):
                continue
            if isinstance(value, str):
                stripped = value.strip()
                if not stripped:
                    values[field_name] = []
                elif stripped.startswith("["):
                    values[field_name] = json.loads(stripped)
                else:
                    values[field_name] = [
                        item.strip() for item in stripped.split(",") if item.strip()
                    ]
        return values

    @model_validator(mode="after")
    def _validate_auth_settings(self) -> "Settings":
        if self.auth_enabled and (
            not self.auth_admin_username.strip() or not self.auth_admin_password.strip()
        ):
            raise ValueError(
                "AUTH_ENABLED requires both AUTH_ADMIN_USERNAME and AUTH_ADMIN_PASSWORD"
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
