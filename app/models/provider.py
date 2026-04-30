from typing import Any

from pydantic import BaseModel, Field


class ProviderSpec(BaseModel):
    type: str
    enabled: bool = True
    class_path: str | None = None
    options: dict[str, Any] = Field(default_factory=dict)
