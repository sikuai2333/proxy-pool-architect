from __future__ import annotations

import re
from collections.abc import Awaitable, Callable
from ipaddress import ip_address
from urllib.parse import urlparse

import httpx

from app.core.config import Settings
from app.models.proxy import ProxyEndpoint
from app.models.url_import import ProxyListFileType, ProxyUrlImportResponse
from app.services.geo_service import GeoResolver
from app.storage.sqlite_store import SQLiteStore
from app.utils.github_mirror import build_mirror_urls, log_mirror_attempt
from app.utils.proxy_text import parse_subscription_content

MAX_PROXY_URL_BYTES = 1_048_576
_SOURCE_SLUG_RE = re.compile(r"[^A-Za-z0-9._-]+")


class ProxyUrlImportError(ValueError):
    def __init__(self, message: str, *, status_code: int) -> None:
        super().__init__(message)
        self.status_code = status_code


class ProxyUrlImportService:
    def __init__(
        self,
        store: SQLiteStore,
        settings: Settings,
        downloader: Callable[[str], Awaitable[str]] | None = None,
    ) -> None:
        self._store = store
        self._settings = settings
        self._geo_resolver = GeoResolver.from_settings(settings)
        self._downloader = downloader or self._download_text

    async def import_from_url(
        self,
        *,
        url: str,
        file_type: ProxyListFileType,
    ) -> ProxyUrlImportResponse:
        self._validate_source_url(url)

        source = self._build_source_label(url, file_type)
        content = await self._downloader(url)
        parsed = parse_subscription_content(content, file_type=file_type, source=source)
        unique_proxies = self._deduplicate(parsed.proxies)

        for proxy in unique_proxies:
            await self._store.add_proxy("raw", self._enrich(proxy))

        return ProxyUrlImportResponse(
            source=source,
            file_type=file_type,
            detected_format=parsed.detected_format,
            fetched_count=parsed.fetched_count,
            valid_count=parsed.valid_count,
            stored_count=len(unique_proxies),
            duplicate_count=max(parsed.direct_supported_count - len(unique_proxies), 0),
            invalid_count=parsed.invalid_count,
            direct_supported_count=parsed.direct_supported_count,
            adapter_required_count=parsed.adapter_required_count,
            unsupported_count=parsed.unsupported_count,
            detected_protocols=parsed.detected_protocols,
            supported_connection_modes=parsed.supported_connection_modes,
        )

    async def _download_text(self, url: str) -> str:
        mirrors = self._settings.github_mirrors or None
        urls_to_try = build_mirror_urls(url, mirrors)

        last_exc: Exception | None = None
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(self._settings.provider_url_timeout_seconds),
            follow_redirects=True,
        ) as client:
            for try_url in urls_to_try:
                if try_url != url:
                    log_mirror_attempt(try_url, url)
                try:
                    response = await client.get(try_url)
                except httpx.HTTPError as exc:
                    last_exc = exc
                    continue

                if response.status_code >= 400:
                    last_exc = RuntimeError(f"HTTP {response.status_code}")
                    continue

                if len(response.content) > MAX_PROXY_URL_BYTES:
                    raise ProxyUrlImportError(
                        f"proxy URL content exceeds {MAX_PROXY_URL_BYTES} bytes",
                        status_code=413,
                    )
                return response.text

        raise ProxyUrlImportError(
            f"failed to fetch proxy URL (tried {len(urls_to_try)} mirrors): "
            f"{last_exc.__class__.__name__ if last_exc else 'unknown'}",
            status_code=502,
        )

    def _validate_source_url(self, url: str) -> None:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            raise ProxyUrlImportError("only http and https URLs are supported", status_code=400)
        if not parsed.hostname:
            raise ProxyUrlImportError("proxy URL host is required", status_code=400)
        if (
            self._settings.safe_block_private_networks
            and _is_private_host(parsed.hostname)
        ):
            raise ProxyUrlImportError(
                "private or local source URLs are blocked by settings",
                status_code=400,
            )

    @staticmethod
    def _build_source_label(url: str, file_type: ProxyListFileType) -> str:
        parsed = urlparse(url)
        host = parsed.hostname or "unknown"
        path_parts = [part for part in parsed.path.split("/") if part]
        slug_parts: list[str] = []

        if host == "raw.githubusercontent.com" and len(path_parts) >= 4:
            slug_parts = [path_parts[0], path_parts[1], path_parts[-1]]
        elif host == "cdn.jsdelivr.net" and len(path_parts) >= 4 and path_parts[0] == "gh":
            repo_part = path_parts[2].split("@", 1)[0]
            slug_parts = [path_parts[1], repo_part, *path_parts[-2:]]
        elif path_parts:
            slug_parts = path_parts[-2:] if len(path_parts) >= 2 else path_parts

        if not slug_parts:
            return f"url_submit:{file_type}:{host}"

        slug = "-".join(
            cleaned
            for cleaned in (_sanitize_source_part(part) for part in slug_parts)
            if cleaned
        )
        if not slug:
            return f"url_submit:{file_type}:{host}"
        return f"url_submit:{file_type}:{host}:{slug}"

    @staticmethod
    def _deduplicate(proxies: list[ProxyEndpoint]) -> list[ProxyEndpoint]:
        seen: set[str] = set()
        deduplicated: list[ProxyEndpoint] = []
        for proxy in proxies:
            if proxy.id in seen:
                continue
            seen.add(proxy.id)
            deduplicated.append(proxy)
        return deduplicated

    def _enrich(self, proxy: ProxyEndpoint) -> ProxyEndpoint:
        if self._geo_resolver is None:
            return proxy
        return self._geo_resolver.enrich(proxy)


def _is_private_host(host: str) -> bool:
    if host.casefold() == "localhost":
        return True

    stripped = host.strip("[]")
    try:
        address = ip_address(stripped)
    except ValueError:
        return False
    return (
        address.is_private
        or address.is_loopback
        or address.is_link_local
        or address.is_multicast
        or address.is_reserved
        or address.is_unspecified
    )


def _sanitize_source_part(value: str) -> str:
    return _SOURCE_SLUG_RE.sub("-", value).strip("-")
