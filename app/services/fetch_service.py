from app.models.provider import ProviderFetchResult
from app.models.proxy import ProxyEndpoint
from app.providers.manager import ProviderManager
from app.services.geo_service import GeoResolver
from app.storage.sqlite_store import SQLiteStore
from app.utils.time import utc_now_iso


class FetchRunReport:
    def __init__(
        self,
        stored: list[ProxyEndpoint],
        provider_results: list[ProviderFetchResult],
        fetched_at: str,
    ) -> None:
        self.stored = stored
        self.provider_results = provider_results
        self.fetched_at = fetched_at


class FetchService:
    def __init__(
        self,
        provider_manager: ProviderManager,
        store: SQLiteStore,
        geo_resolver: GeoResolver | None = None,
    ) -> None:
        self._provider_manager = provider_manager
        self._store = store
        self._geo_resolver = geo_resolver

    async def fetch_to_raw_pool(self) -> list[ProxyEndpoint]:
        report = await self.fetch_to_raw_pool_with_report()
        return report.stored

    async def fetch_to_raw_pool_with_report(self) -> FetchRunReport:
        proxies, provider_results = await self._provider_manager.fetch_all_with_metadata()
        enriched = [self._enrich(proxy) for proxy in proxies]
        deduplicated = self._deduplicate(enriched)

        stored: list[ProxyEndpoint] = []
        for proxy in deduplicated:
            stored.append(await self._store.add_proxy("raw", proxy))
        return FetchRunReport(
            stored=stored,
            provider_results=provider_results,
            fetched_at=utc_now_iso(),
        )

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
