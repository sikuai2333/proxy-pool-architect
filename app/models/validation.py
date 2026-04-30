from typing import Literal

from pydantic import BaseModel, Field

from app.models.proxy import ProxyAnonymity, ProxyEndpoint, ProxyPool

ValidationName = Literal["protocol", "connectivity", "anonymity"]


class ValidationResult(BaseModel):
    validator: ValidationName
    ok: bool
    latency_ms: int | None = Field(default=None, ge=0)
    status_code: int | None = None
    error: str | None = None
    anonymity: ProxyAnonymity | None = None


class ProxyValidationOutcome(BaseModel):
    proxy_id: str
    target_pool: ProxyPool
    proxy: ProxyEndpoint
    protocol: ValidationResult
    connectivity: ValidationResult | None = None
    anonymity: ValidationResult | None = None
