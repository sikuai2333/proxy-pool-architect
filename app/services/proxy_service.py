from app.models.api import ReportProxyRequest
from app.models.proxy import ProxyEndpoint, ProxyFilters, ProxyPool
from app.storage.redis_store import RedisStore
from app.utils.time import utc_now_iso, utc_plus_seconds_iso


class ProxyService:
    def __init__(self, store: RedisStore, cooldown_seconds: int = 1800) -> None:
        self._store = store
        self._cooldown_seconds = cooldown_seconds

    async def get_proxy(self, filters: ProxyFilters) -> ProxyEndpoint | None:
        return await self._store.get_best_proxy(filters)

    async def list_proxies(
        self,
        pool: ProxyPool,
        filters: ProxyFilters,
        limit: int,
        offset: int,
    ) -> list[ProxyEndpoint]:
        scan_limit = max(limit + offset, 100)
        proxies = await self._store.list_proxies(pool, limit=scan_limit, offset=0)
        filtered = [proxy for proxy in proxies if self._matches_filters(proxy, filters)]
        return filtered[offset : offset + limit]

    async def report_result(self, report: ReportProxyRequest) -> ProxyEndpoint | None:
        proxy = await self._store.get_proxy(report.proxy_id)
        pool = await self._store.find_proxy_pool(report.proxy_id)
        if proxy is None or pool is None:
            return None

        now = utc_now_iso()
        if report.ok:
            updates: dict[str, object] = {
                "score": proxy.score + 10,
                "success_count": proxy.success_count + 1,
                "consecutive_fail_count": 0,
                "last_checked_at": now,
                "last_success_at": now,
                "last_error": None,
                "cooldown_until": None,
            }
            if report.latency_ms is not None:
                updates["latency_ms"] = report.latency_ms
            return await self._store.save_proxy(pool, proxy.model_copy(update=updates))

        fail_count = proxy.fail_count + 1
        consecutive_fail_count = proxy.consecutive_fail_count + 1
        updates = {
            "score": proxy.score - 20,
            "fail_count": fail_count,
            "consecutive_fail_count": consecutive_fail_count,
            "last_checked_at": now,
            "last_error": report.error or "reported_failure",
        }
        if report.latency_ms is not None:
            updates["latency_ms"] = report.latency_ms

        updated_proxy = proxy.model_copy(update=updates)
        if consecutive_fail_count >= 5 and pool != "dead":
            await self._store.remove_proxy(pool, proxy.id)
            return await self._store.add_proxy("dead", updated_proxy)
        if consecutive_fail_count >= 3 and pool != "cooldown":
            await self._store.remove_proxy(pool, proxy.id)
            return await self._store.add_proxy(
                "cooldown",
                updated_proxy.model_copy(
                    update={"cooldown_until": utc_plus_seconds_iso(self._cooldown_seconds)}
                ),
            )
        return await self._store.save_proxy(pool, updated_proxy)

    async def delete_proxy(self, proxy_id: str) -> bool:
        return await self._store.delete_proxy(proxy_id)

    @staticmethod
    def _matches_filters(proxy: ProxyEndpoint, filters: ProxyFilters) -> bool:
        if filters.scheme is not None and proxy.scheme != filters.scheme:
            return False
        if filters.anonymity is not None and proxy.anonymity != filters.anonymity:
            return False
        if filters.country is not None and proxy.country != filters.country:
            return False
        return not (filters.min_score is not None and proxy.score < filters.min_score)
