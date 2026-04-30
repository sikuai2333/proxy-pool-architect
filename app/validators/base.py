from abc import ABC, abstractmethod

from app.models.proxy import ProxyEndpoint
from app.models.validation import ValidationResult


class ProxyValidator(ABC):
    @abstractmethod
    async def validate(self, proxy: ProxyEndpoint) -> ValidationResult:
        """Validate a proxy and return a structured result."""
