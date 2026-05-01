from app.models.api import ReportProxyRequest
from app.models.proxy import ProxyEndpoint, ProxyFilters, ProxyPool
from app.storage.redis_store import RedisStore
from app.utils.time import utc_now_iso, utc_plus_seconds_iso


class ProxyService:
    def __init__(
        self,
        store: RedisStore,
        cooldown_seconds: int = 1800,
        session_affinity_ttl_seconds: int = 3600,
    ) -> None:
        self._store = store
        self._cooldown_seconds = cooldown_seconds
        self._session_affinity_ttl_seconds = session_affinity_ttl_seconds

    async def get_proxy(
        self,
        filters: ProxyFilters,
        session_id: str | None = None,
    ) -> ProxyEndpoint | None:
        if session_id is not None:
            pinned_proxy = await self._get_session_proxy(session_id, filters)
            if pinned_proxy is not None:
                return pinned_proxy

        proxy = await self._store.get_best_proxy(filters)
        if proxy is not None and session_id is not None:
            await self._store.bind_session_proxy(
                session_id=session_id,
                proxy_id=proxy.id,
                ttl_seconds=self._session_affinity_ttl_seconds,
            )
        return proxy

    async def list_proxies(
        self,
        pool: ProxyPool | None,
        filters: ProxyFilters,
        limit: int,
        offset: int,
    ) -> tuple[list[ProxyEndpoint], int]:
        return await self._store.list_filtered_proxies(
            pool=pool,
            filters=filters,
            limit=limit,
            offset=offset,
        )

    async def get_proxy_detail(self, proxy_id: str) -> ProxyEndpoint | None:
        return await self._store.get_proxy(proxy_id)

    async def report_result(self, report: ReportProxyRequest) -> ProxyEndpoint | None:
        record = await self._store.get_proxy_record(report.proxy_id)
        if record is None:
            return None
        pool, proxy = record

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

    async def _get_session_proxy(
        self,
        session_id: str,
        filters: ProxyFilters,
    ) -> ProxyEndpoint | None:
        proxy_id = await self._store.get_session_proxy_id(session_id)
        if proxy_id is None:
            return None

        proxy = await self._store.get_proxy(proxy_id)
        if proxy is None:
            return None
        if proxy.status not in {"checked", "elite"}:
            return None
        if not self._matches_filters(proxy, filters):
            return None
        return proxy

    @staticmethod
    def _matches_filters(proxy: ProxyEndpoint, filters: ProxyFilters) -> bool:
        if filters.scheme is not None and proxy.scheme != filters.scheme:
            return False
        if filters.anonymity is not None and proxy.anonymity != filters.anonymity:
            return False
        if filters.country is not None and proxy.country != filters.country:
            return False
        if filters.source is not None and proxy.source != filters.source:
            return False
        if filters.query is not None:
            query = filters.query.strip().casefold()
            if query and query not in proxy.host.casefold() and query not in proxy.id.casefold():
                return False
        return not (filters.min_score is not None and proxy.score < filters.min_score)
