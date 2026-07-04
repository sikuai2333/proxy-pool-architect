import asyncio
from datetime import UTC, datetime, timedelta

from app.models.proxy import ProxyEndpoint
from app.services.cooldown_service import CooldownService
from app.storage.sqlite_store import SQLiteStore


def make_proxy(proxy_id: str, cooldown_until: str | None) -> ProxyEndpoint:
    return ProxyEndpoint(
        id=proxy_id,
        scheme="http",
        host="1.2.3.4",
        port=8080,
        source="test",
        cooldown_until=cooldown_until,
    )


def test_cooldown_service_releases_expired_proxies_to_raw_pool() -> None:
    async def run() -> None:
        store = SQLiteStore(":memory:")
        expired = (datetime.now(UTC) - timedelta(seconds=1)).isoformat()
        future = (datetime.now(UTC) + timedelta(seconds=300)).isoformat()
        await store.add_proxy("cooldown", make_proxy("http-1.2.3.4-8080", expired))
        await store.add_proxy("cooldown", make_proxy("http-1.2.3.5-8080", future))

        released = await CooldownService(store).release_expired()

        assert [proxy.id for proxy in released] == ["http-1.2.3.4-8080"]
        assert [proxy.id for proxy in await store.list_proxies("raw")] == ["http-1.2.3.4-8080"]
        assert [proxy.id for proxy in await store.list_proxies("cooldown")] == [
            "http-1.2.3.5-8080"
        ]

    asyncio.run(run())
