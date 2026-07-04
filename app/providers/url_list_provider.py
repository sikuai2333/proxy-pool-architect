import asyncio
from urllib.parse import urlparse

import httpx
from loguru import logger

from app.models.proxy import ProxyEndpoint
from app.providers.base import ProxyProvider
from app.utils.github_mirror import build_mirror_urls, log_mirror_attempt
from app.utils.proxy_text import extract_proxies_from_text


class UrlListProvider(ProxyProvider):
    def __init__(
        self,
        urls: list[str],
        name: str = "url_lists",
        enabled: bool = True,
        timeout_seconds: float = 10.0,
        concurrency: int = 5,
        github_mirrors: list[str] | None = None,
    ) -> None:
        self.name = name
        self._urls = urls
        self.enabled = enabled
        self._timeout = httpx.Timeout(timeout_seconds)
        self._semaphore = asyncio.Semaphore(concurrency)
        self._github_mirrors = github_mirrors

    async def fetch(self) -> list[ProxyEndpoint]:
        if not self.enabled:
            return []

        async with httpx.AsyncClient(
            timeout=self._timeout, follow_redirects=True
        ) as client:
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
        urls_to_try = build_mirror_urls(url, self._github_mirrors)

        async with self._semaphore:
            for try_url in urls_to_try:
                if try_url != url:
                    log_mirror_attempt(try_url, url)
                try:
                    response = await client.get(try_url)
                except httpx.HTTPError as exc:
                    logger.debug(
                        "Failed to fetch {} from {}: {}",
                        url_label,
                        self._safe_url_label(try_url),
                        exc.__class__.__name__,
                    )
                    continue

                if response.status_code >= 400:
                    logger.debug(
                        "Skipping {} from {} due to status {}",
                        url_label,
                        self._safe_url_label(try_url),
                        response.status_code,
                    )
                    continue

                return self._parse_lines(response.text, url_label)

        logger.warning("All mirrors failed for proxy URL list from {}", url_label)
        return []

    def _parse_lines(self, content: str, source_label: str) -> list[ProxyEndpoint]:
        result = extract_proxies_from_text(content, file_type="all", source=self.name)
        if result.invalid_count:
            logger.warning(
                "Skipped {} invalid proxy entries from {}",
                result.invalid_count,
                source_label,
            )
        return result.proxies

    @staticmethod
    def _safe_url_label(url: str) -> str:
        parsed = urlparse(url)
        return parsed.hostname or "<configured url>"
