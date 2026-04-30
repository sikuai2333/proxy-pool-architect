from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


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
    log_level: str = "INFO"
    redis_url: str = "redis://localhost:6379/0"

    provider_static_enabled: bool = True
    provider_static_proxies: list[str] = Field(default_factory=list)
    provider_url_lists_enabled: bool = False
    provider_url_list_urls: list[str] = Field(default_factory=list)
    provider_url_timeout_seconds: float = Field(default=10.0, gt=0)
    provider_url_concurrency: int = Field(default=5, ge=1)

    validate_concurrency: int = Field(default=100, ge=1)
    validate_timeout_seconds: float = Field(default=10.0, gt=0)
    test_url: str = "https://httpbin.org/ip"
    anonymity_test_url: str = "https://httpbin.org/headers"
    validator_original_ip: str | None = None
    min_elite_score: int = 80


@lru_cache
def get_settings() -> Settings:
    return Settings()
