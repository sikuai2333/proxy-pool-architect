import asyncio
from collections.abc import Mapping

from app.models.proxy import ProxyEndpoint
from app.providers.manager import ProviderManager
from app.providers.static_provider import StaticProvider
from app.providers.url_list_provider import UrlListProvider
from app.services.fetch_service import FetchService
from app.storage.redis_store import RedisStore


class FakeRedis:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}
        self.sorted_sets: dict[str, dict[str, float]] = {}

    async def set(self, name: str, value: str) -> bool:
        self.values[name] = value
        return True

    async def get(self, name: str) -> str | None:
        return self.values.get(name)

    async def delete(self, *names: str) -> int:
        removed = 0
        for name in names:
            if name in self.values:
                removed += 1
                del self.values[name]
        return removed

    async def zadd(self, name: str, mapping: Mapping[str, float]) -> int:
        sorted_set = self.sorted_sets.setdefault(name, {})
        added = 0
        for member, score in mapping.items():
            if member not in sorted_set:
                added += 1
            sorted_set[member] = score
        return added

    async def zrem(self, name: str, *values: str) -> int:
        sorted_set = self.sorted_sets.setdefault(name, {})
        removed = 0
        for value in values:
            if value in sorted_set:
                removed += 1
                del sorted_set[value]
        return removed

    async def zcard(self, name: str) -> int:
        return len(self.sorted_sets.get(name, {}))

    async def zrevrange(self, name: str, start: int, end: int) -> list[str]:
        sorted_set = self.sorted_sets.get(name, {})
        members = sorted(sorted_set, key=lambda member: (-sorted_set[member], member))
        stop = None if end == -1 else end + 1
        return members[start:stop]

    async def zincrby(self, name: str, amount: float, value: str) -> float:
        sorted_set = self.sorted_sets.setdefault(name, {})
        sorted_set[value] = sorted_set.get(value, 0.0) + amount
        return sorted_set[value]


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
