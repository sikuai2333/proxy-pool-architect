from app.models.proxy import ProxyEndpoint
from app.providers.base import ProxyProvider
from app.utils.proxy_url import build_proxy_id


class TorProvider(ProxyProvider):
    name = "tor"

    def __init__(
        self,
        socks_host: str = "127.0.0.1",
        socks_port: int = 9050,
        enabled: bool = True,
    ) -> None:
        self._socks_host = socks_host
        self._socks_port = socks_port
        self.enabled = enabled

    async def fetch(self) -> list[ProxyEndpoint]:
        if not self.enabled:
            return []
        return [
            ProxyEndpoint(
                id=build_proxy_id("socks5", self._socks_host, self._socks_port),
                scheme="socks5",
                host=self._socks_host,
                port=self._socks_port,
                source=self.name,
            )
        ]
