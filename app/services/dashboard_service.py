from collections import Counter

from app.models.api import ProxyResponse
from app.models.dashboard import DashboardView, SourceDistributionItem
from app.storage.keys import POOL_NAMES
from app.storage.redis_store import RedisStore


class DashboardService:
    def __init__(self, store: RedisStore) -> None:
        self._store = store

    async def get_dashboard(self, proxy_limit: int = 100) -> DashboardView:
        pools = await self._store.count_by_pool()
        proxies = []
        for pool in POOL_NAMES:
            proxies.extend(await self._store.list_proxies(pool, limit=proxy_limit, offset=0))

        total = sum(pools.values())
        latencies = [proxy.latency_ms for proxy in proxies if proxy.latency_ms is not None]
        attempts = sum(proxy.success_count + proxy.fail_count for proxy in proxies)
        successes = sum(proxy.success_count for proxy in proxies)
        sources = Counter(proxy.source for proxy in proxies)

        return DashboardView(
            pools={pool: pools.get(pool, 0) for pool in POOL_NAMES},
            total=total,
            average_latency_ms=sum(latencies) / len(latencies) if latencies else None,
            success_rate=successes / attempts if attempts else None,
            sources=[
                SourceDistributionItem(source=source, count=count)
                for source, count in sorted(sources.items())
            ],
            proxies=[
                ProxyResponse.from_endpoint(proxy)
                for proxy in sorted(proxies, key=lambda item: item.score, reverse=True)
            ][:proxy_limit],
        )
