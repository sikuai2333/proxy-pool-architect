import asyncio
from urllib.parse import urlparse

import httpx
from loguru import logger

from app.models.proxy import ProxyEndpoint
from app.providers.base import ProxyProvider
from app.utils.proxy_url import ProxyUrlParseError, parse_proxy_url


class UrlListProvider(ProxyProvider):
    name = "url_lists"

    def __init__(
        self,
        urls: list[str],
        enabled: bool = True,
        timeout_seconds: float = 10.0,
        concurrency: int = 5,
    ) -> None:
        self._urls = urls
        self.enabled = enabled
        self._timeout = httpx.Timeout(timeout_seconds)
        self._semaphore = asyncio.Semaphore(concurrency)

    async def fetch(self) -> list[ProxyEndpoint]:
        if not self.enabled:
            return []

        async with httpx.AsyncClient(timeout=self._timeout, follow_redirects=False) as client:
            results = await asyncio.gather(
                *(self._fetch_url(client, url) for url in self._urls),
                return_exceptions=False,
            )

        proxies: list[ProxyEndpoint] = []
        for result in results:
            proxies.extend(result)
        return proxies

    async def _fetch_url(self, client: httpx.AsyncClient, url: str) -> list[ProxyEndpoint]:
        url_label = self._safe_url_label(url)
        async with self._semaphore:
            try:
                response = await client.get(url)
            except httpx.HTTPError as exc:
                logger.warning(
                    "Failed to fetch proxy URL list from {}: {}",
                    url_label,
                    exc.__class__.__name__,
                )
                return []

        if response.status_code in {403, 429}:
            logger.warning(
                "Skipping proxy URL list from {} due to status {}",
                url_label,
                response.status_code,
            )
            return []
        if response.status_code >= 400:
            logger.warning(
                "Skipping proxy URL list from {} due to status {}",
                url_label,
                response.status_code,
            )
            return []

        return self._parse_lines(response.text, url_label)

    def _parse_lines(self, content: str, source_label: str) -> list[ProxyEndpoint]:
        proxies: list[ProxyEndpoint] = []
        for raw_line in content.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                proxies.append(parse_proxy_url(line, self.name))
            except ProxyUrlParseError as exc:
                logger.warning("Skipping invalid proxy from {}: {}", source_label, exc)
        return proxies

    @staticmethod
    def _safe_url_label(url: str) -> str:
        parsed = urlparse(url)
        return parsed.hostname or "<configured url>"
