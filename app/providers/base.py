from abc import ABC, abstractmethod

from app.models.proxy import ProxyEndpoint


class ProxyProvider(ABC):
    name: str
    enabled: bool

    @abstractmethod
    async def fetch(self) -> list[ProxyEndpoint]:
        """Fetch candidate proxies from this provider."""
