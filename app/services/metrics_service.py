from collections import Counter

from app.storage.keys import POOL_NAMES
from app.storage.redis_store import RedisStore

METRICS_CONTENT_TYPE = "text/plain; version=0.0.4; charset=utf-8"


class MetricsService:
    def __init__(self, store: RedisStore) -> None:
        self._store = store

    async def render_prometheus(self) -> str:
        pools = await self._store.count_by_pool()
        proxies = []
        for pool in POOL_NAMES:
            proxies.extend(await self._store.list_proxies(pool, limit=1000, offset=0))

        latencies = [proxy.latency_ms for proxy in proxies if proxy.latency_ms is not None]
        attempts = sum(proxy.success_count + proxy.fail_count for proxy in proxies)
        successes = sum(proxy.success_count for proxy in proxies)
        source_counts = Counter(proxy.source for proxy in proxies)

        lines = [
            "# HELP proxy_pool_proxies Number of proxies by pool.",
            "# TYPE proxy_pool_proxies gauge",
        ]
        for pool in POOL_NAMES:
            lines.append(f'proxy_pool_proxies{{pool="{pool}"}} {pools.get(pool, 0)}')

        lines.extend(
            [
                "# HELP proxy_pool_total_proxies Total number of stored proxies.",
                "# TYPE proxy_pool_total_proxies gauge",
                f"proxy_pool_total_proxies {sum(pools.values())}",
                "# HELP proxy_pool_average_latency_ms "
                "Average latency for proxies with latency data.",
                "# TYPE proxy_pool_average_latency_ms gauge",
                f"proxy_pool_average_latency_ms {_average(latencies)}",
                "# HELP proxy_pool_success_rate Success rate across stored proxy attempts.",
                "# TYPE proxy_pool_success_rate gauge",
                f"proxy_pool_success_rate {_success_rate(successes, attempts)}",
                "# HELP proxy_pool_source_proxies Number of proxies by provider source.",
                "# TYPE proxy_pool_source_proxies gauge",
            ]
        )
        for source, count in sorted(source_counts.items()):
            lines.append(f'proxy_pool_source_proxies{{source="{_escape_label(source)}"}} {count}')

        return "\n".join(lines) + "\n"


def _average(values: list[int]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def _success_rate(successes: int, attempts: int) -> float:
    if attempts == 0:
        return 0.0
    return successes / attempts


def _escape_label(value: str) -> str:
    return value.replace("\\", "\\\\").replace("\n", "\\n").replace('"', '\\"')
