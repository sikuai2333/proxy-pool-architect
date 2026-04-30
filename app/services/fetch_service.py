from app.models.proxy import ProxyEndpoint
from app.providers.manager import ProviderManager
from app.storage.redis_store import RedisStore


class FetchService:
    def __init__(self, provider_manager: ProviderManager, store: RedisStore) -> None:
        self._provider_manager = provider_manager
        self._store = store

    async def fetch_to_raw_pool(self) -> list[ProxyEndpoint]:
        proxies = await self._provider_manager.fetch_all()
        deduplicated = self._deduplicate(proxies)

        stored: list[ProxyEndpoint] = []
        for proxy in deduplicated:
            stored.append(await self._store.add_proxy("raw", proxy))
        return stored

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
