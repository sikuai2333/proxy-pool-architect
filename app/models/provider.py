from typing import Any

from pydantic import BaseModel, Field


class ProviderSpec(BaseModel):
    type: str
    enabled: bool = True
    class_path: str | None = None
    options: dict[str, Any] = Field(default_factory=dict)


class ProviderFetchResult(BaseModel):
    name: str
    enabled: bool
    fetched_count: int = 0
    error: str | None = None
