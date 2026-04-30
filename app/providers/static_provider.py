from loguru import logger

from app.models.proxy import ProxyEndpoint
from app.providers.base import ProxyProvider
from app.utils.proxy_url import ProxyUrlParseError, parse_proxy_url


class StaticProvider(ProxyProvider):
    name = "static"

    def __init__(self, proxies: list[str], enabled: bool = True) -> None:
        self._proxies = proxies
        self.enabled = enabled

    async def fetch(self) -> list[ProxyEndpoint]:
        if not self.enabled:
            return []

        parsed_proxies: list[ProxyEndpoint] = []
        for proxy_url in self._proxies:
            try:
                parsed_proxies.append(parse_proxy_url(proxy_url, self.name))
            except ProxyUrlParseError as exc:
                logger.warning("Skipping invalid static proxy: {}", exc)
        return parsed_proxies
