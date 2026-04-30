from pydantic import BaseModel

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
