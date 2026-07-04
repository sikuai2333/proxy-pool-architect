import asyncio

import pytest

from app.core.config import Settings
from app.services.url_import_service import ProxyUrlImportError, ProxyUrlImportService
from app.storage.sqlite_store import SQLiteStore


def test_url_import_service_fetches_deduplicates_and_stores_raw_proxies() -> None:
    async def downloader(_: str) -> str:
        return """
        1.2.3.4:8080
        1.2.3.4:8080
        invalid
        https://5.6.7.8:8443
        """

    async def run() -> None:
        store = SQLiteStore(":memory:")
        service = ProxyUrlImportService(
            store=store,
            settings=Settings(),
            downloader=downloader,
        )

        result = await service.import_from_url(
            url="https://example.com/http.txt",
            file_type="http",
        )
        raw_pool = await store.list_proxies("raw", limit=10, offset=0)

        assert result.source == "url_submit:http:example.com:http.txt"
        assert result.detected_format == "plain_text"
        assert result.fetched_count == 4
        assert result.valid_count == 3
        assert result.stored_count == 2
        assert result.duplicate_count == 1
        assert result.invalid_count == 1
        assert result.direct_supported_count == 3
        assert result.adapter_required_count == 0
        assert result.unsupported_count == 0
        assert result.detected_protocols == ["http", "https"]
        assert result.supported_connection_modes == ["direct"]
        assert [proxy.id for proxy in raw_pool] == [
            "http-1.2.3.4-8080",
            "https-5.6.7.8-8443",
        ]

    asyncio.run(run())


def test_url_import_service_blocks_private_source_urls_when_enabled() -> None:
    async def run() -> None:
        service = ProxyUrlImportService(
            store=SQLiteStore(":memory:"),
            settings=Settings(),
            downloader=lambda _: _resolve("1.2.3.4:8080"),
        )

        with pytest.raises(ProxyUrlImportError) as exc_info:
            await service.import_from_url(
                url="http://127.0.0.1/http.txt",
                file_type="http",
            )

        assert exc_info.value.status_code == 400

    asyncio.run(run())


def test_url_import_service_reports_v2ray_nodes_as_adapter_required() -> None:
    async def downloader(_: str) -> str:
        return (
            "vmess://eyJhZGQiOiIxLjIuMy40IiwicG9ydCI6IjQ0MyIsImlkIjoidXVpZCJ9\n"
            "trojan://secret@5.6.7.8:443#demo\n"
        )

    async def run() -> None:
        store = SQLiteStore(":memory:")
        service = ProxyUrlImportService(
            store=store,
            settings=Settings(),
            downloader=downloader,
        )

        result = await service.import_from_url(
            url="https://example.com/subscription.txt",
            file_type="v2ray",
        )

        assert result.detected_format == "v2ray_uri_list"
        assert result.valid_count == 2
        assert result.stored_count == 0
        assert result.direct_supported_count == 0
        assert result.adapter_required_count == 2
        assert result.detected_protocols == ["trojan", "vmess"]
        assert result.supported_connection_modes == ["core_adapter"]
        assert await store.list_proxies("raw", limit=10, offset=0) == []

    asyncio.run(run())


async def _resolve(value: str) -> str:
    return value


def test_url_import_service_builds_distinct_source_labels_for_raw_github_urls() -> None:
    assert ProxyUrlImportService._build_source_label(
        "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt",
        "http",
    ) == "url_submit:http:raw.githubusercontent.com:TheSpeedX-SOCKS-List-http.txt"


def test_url_import_service_builds_distinct_source_labels_for_jsdelivr_urls() -> None:
    assert ProxyUrlImportService._build_source_label(
        "https://cdn.jsdelivr.net/gh/proxifly/free-proxy-list@main/proxies/protocols/socks5/data.txt",
        "all",
    ) == "url_submit:all:cdn.jsdelivr.net:proxifly-free-proxy-list-socks5-data.txt"
