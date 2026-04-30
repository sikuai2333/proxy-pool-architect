import asyncio
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx
import yaml
from loguru import logger

from app.models.proxy import ProxyEndpoint, ProxyScheme
from app.providers.base import ProxyProvider
from app.utils.proxy_url import ProxyUrlParseError, build_proxy_id, parse_proxy_url

CLASH_TYPE_TO_SCHEME: dict[str, ProxyScheme] = {
    "http": "http",
    "socks4": "socks4",
    "socks5": "socks5",
}


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
        try:
            payload = yaml.safe_load(content)
        except yaml.YAMLError:
            payload = None
        if isinstance(payload, dict) and isinstance(payload.get("proxies"), list):
            return self._parse_clash_nodes(payload["proxies"], source_label)

        return self._parse_text_lines(content, source_label)

    def _parse_clash_nodes(
        self,
        nodes: list[Any],
        source_label: str,
    ) -> list[ProxyEndpoint]:
        proxies: list[ProxyEndpoint] = []
        for node in nodes:
            if not isinstance(node, dict):
                continue
            parsed = self._parse_node(node)
            if parsed is None:
                node_type = str(node.get("type", "<missing>"))
                logger.info(
                    "Skipping unsupported Clash node type from {}: {}",
                    source_label,
                    node_type,
                )
                continue
            proxies.append(parsed)
        return proxies

    def _parse_node(self, node: dict[str, Any]) -> ProxyEndpoint | None:
        node_type = str(node.get("type", "")).lower()
        scheme = CLASH_TYPE_TO_SCHEME.get(node_type)
        if scheme is None:
            return None

        server = node.get("server")
        port = node.get("port")
        if server is None or port is None:
            return None
        try:
            parsed_port = int(port)
        except (TypeError, ValueError):
            return None

        username = node.get("username") or node.get("user")
        password = node.get("password") or node.get("pass")
        return ProxyEndpoint(
            id=build_proxy_id(scheme, str(server), parsed_port),
            scheme=scheme,
            host=str(server),
            port=parsed_port,
            username=str(username) if username is not None else None,
            password=str(password) if password is not None else None,
            source=self.name,
        )

    def _parse_text_lines(self, content: str, source_label: str) -> list[ProxyEndpoint]:
        proxies: list[ProxyEndpoint] = []
        for raw_line in content.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                proxies.append(parse_proxy_url(line, self.name))
            except ProxyUrlParseError as exc:
                logger.warning("Skipping invalid subscription proxy from {}: {}", source_label, exc)
        return proxies

    @staticmethod
    def _safe_url_label(url: str) -> str:
        parsed = urlparse(url)
        return parsed.hostname or "<configured url>"
