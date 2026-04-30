from typing import Literal

from pydantic import BaseModel, Field

ProxyScheme = Literal["http", "https", "socks4", "socks5"]
ProxyAnonymity = Literal["unknown", "transparent", "anonymous", "elite"]
ProxyPool = Literal["raw", "checked", "elite", "dead", "cooldown"]
ProxyStatus = Literal["raw", "checked", "elite", "dead", "cooldown"]


class ProxyEndpoint(BaseModel):
    id: str = Field(min_length=1)
    scheme: ProxyScheme
    host: str = Field(min_length=1)
    port: int = Field(ge=1, le=65535)
    username: str | None = None
    password: str | None = Field(default=None, repr=False)

    source: str = Field(min_length=1)
    country: str | None = None
    asn: str | None = None
    anonymity: ProxyAnonymity = "unknown"

    latency_ms: int | None = Field(default=None, ge=0)
    success_count: int = Field(default=0, ge=0)
    fail_count: int = Field(default=0, ge=0)
    consecutive_fail_count: int = Field(default=0, ge=0)
    score: int = 0

    last_checked_at: str | None = None
    last_success_at: str | None = None
    last_error: str | None = None
    cooldown_until: str | None = None

    status: ProxyStatus = "raw"


class ProxyFilters(BaseModel):
    scheme: ProxyScheme | None = None
    anonymity: ProxyAnonymity | None = None
    country: str | None = None
    min_score: int | None = None
