from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: Literal["ok"]
    app: str
    version: str
    environment: str
    db_configured: bool
    db: Literal["ok", "error", "unknown"] = "unknown"
    scheduler: Literal["running", "stopped", "unknown"] = "unknown"
