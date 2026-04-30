import asyncio

from app.models.proxy import ProxyEndpoint
from app.providers.manager import ProviderManager
from app.providers.static_provider import StaticProvider
from app.providers.url_list_provider import UrlListProvider
from app.services.fetch_service import FetchService
from app.storage.redis_store import RedisStore
from tests.fakes import FakeRedis


def test_static_provider_parses_configured_proxies() -> None:
    async def run() -> None:
        provider = StaticProvider(
            proxies=[
                "http://1.2.3.4:8080",
                "invalid",
                "socks5://user:pass@1.2.3.4:1080",
            ]
        )

        proxies = await provider.fetch()

        assert [proxy.id for proxy in proxies] == [
            "http-1.2.3.4-8080",
            "socks5-1.2.3.4-1080",
        ]

    asyncio.run(run())


def test_url_list_provider_parses_text_lines() -> None:
    provider = UrlListProvider(urls=[], enabled=True)

    proxies = provider._parse_lines(
        """
        # comment
        http://1.2.3.4:8080
        not-a-proxy
        https://1.2.3.4:8443
        """,
        source_label="test-source",
    )

    assert [proxy.id for proxy in proxies] == [
        "http-1.2.3.4-8080",
        "https-1.2.3.4-8443",
    ]


def test_provider_manager_fetches_enabled_providers_only() -> None:
    async def run() -> None:
        enabled = StaticProvider(["http://1.2.3.4:8080"], enabled=True)
        disabled = StaticProvider(["http://1.2.3.5:8080"], enabled=False)
        manager = ProviderManager([enabled, disabled])

        proxies = await manager.fetch_all()

        assert [proxy.id for proxy in proxies] == ["http-1.2.3.4-8080"]

    asyncio.run(run())


def test_fetch_service_deduplicates_and_writes_to_raw_pool() -> None:
    async def run() -> None:
        store = RedisStore(FakeRedis())
        manager = ProviderManager(
            [
                StaticProvider(
                    [
                        "http://1.2.3.4:8080",
                        "http://1.2.3.4:8080",
                        "https://1.2.3.4:8443",
                    ]
                )
            ]
        )
        service = FetchService(manager, store)

        stored = await service.fetch_to_raw_pool()
        raw_pool = await store.list_proxies("raw")

        assert [proxy.id for proxy in stored] == [
            "http-1.2.3.4-8080",
            "https-1.2.3.4-8443",
        ]
        assert all(isinstance(proxy, ProxyEndpoint) for proxy in raw_pool)
        assert {proxy.status for proxy in raw_pool} == {"raw"}

    asyncio.run(run())
