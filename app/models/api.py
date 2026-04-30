from typing import Literal

from pydantic import BaseModel, Field

from app.models.proxy import ProxyAnonymity, ProxyEndpoint, ProxyPool, ProxyScheme, ProxyStatus

ProxyResponseFormat = Literal["json", "text"]


class ProxyResponse(BaseModel):
    id: str
    scheme: ProxyScheme
    host: str
    port: int
    auth_required: bool
    source: str
    country: str | None = None
    asn: str | None = None
    anonymity: ProxyAnonymity
    latency_ms: int | None = None
    success_count: int
    fail_count: int
    score: int
    last_checked_at: str | None = None
    last_success_at: str | None = None
    last_error: str | None = None
    status: ProxyStatus

    @classmethod
    def from_endpoint(cls, proxy: ProxyEndpoint) -> "ProxyResponse":
        return cls(
            id=proxy.id,
            scheme=proxy.scheme,
            host=proxy.host,
            port=proxy.port,
            auth_required=proxy.username is not None or proxy.password is not None,
            source=proxy.source,
            country=proxy.country,
            asn=proxy.asn,
            anonymity=proxy.anonymity,
            latency_ms=proxy.latency_ms,
            success_count=proxy.success_count,
            fail_count=proxy.fail_count,
            score=proxy.score,
            last_checked_at=proxy.last_checked_at,
            last_success_at=proxy.last_success_at,
            last_error=proxy.last_error,
            status=proxy.status,
        )


class ProxyListResponse(BaseModel):
    proxies: list[ProxyResponse]
    count: int
    limit: int = Field(ge=1)
    offset: int = Field(ge=0)


class ReportProxyRequest(BaseModel):
    proxy_id: str = Field(min_length=1)
    ok: bool
    latency_ms: int | None = Field(default=None, ge=0)
    error: str | None = None


class ReportProxyResponse(BaseModel):
    proxy_id: str
    status: ProxyStatus
    score: int
    success_count: int
    fail_count: int


class DeleteProxyResponse(BaseModel):
    proxy_id: str
    deleted: bool


class StatsResponse(BaseModel):
    pools: dict[ProxyPool, int]
    total: int
    average_latency_ms: float | None = None
    success_rate: float | None = None
