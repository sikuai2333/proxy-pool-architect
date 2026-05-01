from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: Literal["ok"]
    app: str
    version: str
    environment: str
    redis_configured: bool
    redis: Literal["ok", "error", "unknown"] = "unknown"
    scheduler: Literal["running", "stopped", "unknown"] = "unknown"
