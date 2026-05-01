from typing import Literal

from pydantic import BaseModel, Field

from app.models.api import ProxyResponse
from app.models.proxy import ProxyPool


class SourceDistributionItem(BaseModel):
    source: str
    count: int


class DashboardView(BaseModel):
    pools: dict[ProxyPool, int]
    total: int
    average_latency_ms: float | None
    success_rate: float | None
    sources: list[SourceDistributionItem]
    proxies: list[ProxyResponse]


class ProviderSummary(BaseModel):
    name: str
    enabled: bool
    last_fetch_at: str | None = None
    fetched_count: int = Field(default=0, ge=0)
    valid_count: int = Field(default=0, ge=0)
    last_error: str | None = None


class ProviderListResponse(BaseModel):
    items: list[ProviderSummary]


class GeoCountrySummary(BaseModel):
    country: str
    total: int = Field(ge=0)
    elite: int = Field(ge=0)
    avg_latency_ms: float | None = Field(default=None, ge=0)


class GeoAsnSummary(BaseModel):
    asn: str
    total: int = Field(ge=0)
    elite: int = Field(ge=0)
    avg_latency_ms: float | None = Field(default=None, ge=0)


class GeoSummaryResponse(BaseModel):
    countries: list[GeoCountrySummary]
    asns: list[GeoAsnSummary]


ValidationJobStatus = Literal["running", "finished", "failed"]
EventLevel = Literal["info", "warning", "error"]


class ValidationJob(BaseModel):
    id: str
    started_at: str
    finished_at: str | None = None
    checked_count: int = Field(default=0, ge=0)
    success_count: int = Field(default=0, ge=0)
    fail_count: int = Field(default=0, ge=0)
    timeout_count: int = Field(default=0, ge=0)
    status: ValidationJobStatus


class ValidationJobListResponse(BaseModel):
    items: list[ValidationJob]


class EventLogEntry(BaseModel):
    id: str
    type: str
    level: EventLevel
    message: str
    created_at: str


class EventListResponse(BaseModel):
    items: list[EventLogEntry]


class SafeNetworkingSettings(BaseModel):
    authorized_targets_only: bool = True
    block_private_networks: bool = True
    mask_proxy_credentials: bool = True


class DashboardSettings(BaseModel):
    fetch_interval_seconds: int = Field(ge=1)
    validate_interval_seconds: int = Field(ge=1)
    validate_timeout_seconds: float = Field(gt=0)
    validate_concurrency: int = Field(ge=1)
    min_elite_score: int
    cooldown_seconds: int = Field(ge=1)
    safe_networking: SafeNetworkingSettings = Field(default_factory=SafeNetworkingSettings)
