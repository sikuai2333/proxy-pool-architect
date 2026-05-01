import asyncio
from pathlib import Path
from urllib.parse import urlparse

import httpx
from loguru import logger

from app.models.proxy import ProxyEndpoint
from app.providers.base import ProxyProvider
from app.utils.proxy_text import parse_subscription_content


class ClashSubscriptionProvider(ProxyProvider):
    name = "clash_subscription"

    def __init__(
        self,
        urls: list[str],
        files: list[str],
        enabled: bool = True,
        timeout_seconds: float = 10.0,
        concurrency: int = 3,
    ) -> None:
        self._urls = urls
        self._files = files
        self.enabled = enabled
        self._timeout = httpx.Timeout(timeout_seconds)
        self._semaphore = asyncio.Semaphore(concurrency)

    async def fetch(self) -> list[ProxyEndpoint]:
        if not self.enabled:
            return []

        proxies: list[ProxyEndpoint] = []
        for file_path in self._files:
            proxies.extend(self._fetch_file(file_path))

        async with httpx.AsyncClient(timeout=self._timeout, follow_redirects=False) as client:
            results = await asyncio.gather(
                *(self._fetch_url(client, url) for url in self._urls),
                return_exceptions=False,
            )
        for result in results:
            proxies.extend(result)
        return proxies

    def _fetch_file(self, file_path: str) -> list[ProxyEndpoint]:
        path = Path(file_path)
        if not path.exists():
            logger.warning("Skipping missing Clash subscription file: {}", path.name)
            return []
        return self._parse_subscription(path.read_text(encoding="utf-8"), source_label=path.name)

    async def _fetch_url(self, client: httpx.AsyncClient, url: str) -> list[ProxyEndpoint]:
        url_label = self._safe_url_label(url)
        async with self._semaphore:
            try:
                response = await client.get(url)
            except httpx.HTTPError as exc:
                logger.warning(
                    "Failed to fetch Clash subscription from {}: {}",
                    url_label,
                    exc.__class__.__name__,
                )
                return []

        if response.status_code in {403, 429} or response.status_code >= 400:
            logger.warning(
                "Skipping Clash subscription from {} due to status {}",
                url_label,
                response.status_code,
            )
            return []
        return self._parse_subscription(response.text, source_label=url_label)

    def _parse_subscription(self, content: str, source_label: str) -> list[ProxyEndpoint]:
        result = parse_subscription_content(content, file_type="auto", source=self.name)
        if result.adapter_required_count:
            logger.info(
                "Detected {} adapter-required subscription nodes from {}",
                result.adapter_required_count,
                source_label,
            )
        if result.unsupported_count:
            logger.info(
                "Skipped {} unsupported subscription nodes from {}",
                result.unsupported_count,
                source_label,
            )
        if result.invalid_count:
            logger.warning(
                "Skipped {} invalid subscription entries from {}",
                result.invalid_count,
                source_label,
            )
        return result.proxies

    @staticmethod
    def _safe_url_label(url: str) -> str:
        parsed = urlparse(url)
        return parsed.hostname or "<configured url>"
