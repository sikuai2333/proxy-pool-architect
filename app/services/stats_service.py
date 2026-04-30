from app.models.api import StatsResponse
from app.storage.keys import POOL_NAMES
from app.storage.redis_store import RedisStore


class StatsService:
    def __init__(self, store: RedisStore) -> None:
        self._store = store

    async def get_stats(self) -> StatsResponse:
        pools = await self._store.count_by_pool()
        proxies = []
        for pool in POOL_NAMES:
            proxies.extend(await self._store.list_proxies(pool, limit=1000, offset=0))

        total = sum(pools.values())
        latencies = [proxy.latency_ms for proxy in proxies if proxy.latency_ms is not None]
        attempts = sum(proxy.success_count + proxy.fail_count for proxy in proxies)
        successes = sum(proxy.success_count for proxy in proxies)

        average_latency = sum(latencies) / len(latencies) if latencies else None
        success_rate = successes / attempts if attempts else None

        return StatsResponse(
            pools={pool: pools.get(pool, 0) for pool in POOL_NAMES},
            total=total,
            average_latency_ms=average_latency,
            success_rate=success_rate,
        )
