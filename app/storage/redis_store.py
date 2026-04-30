from collections.abc import Mapping
from typing import Any, Protocol, cast

from redis.asyncio import Redis

from app.models.proxy import ProxyEndpoint, ProxyFilters, ProxyPool
from app.storage.keys import (
    POOL_NAMES,
    SELECTION_POOLS,
    pool_index_key,
    proxy_key,
    proxy_pool_key,
    session_proxy_key,
)
from app.storage.serializers import deserialize_proxy, serialize_proxy


class RedisClient(Protocol):
    async def set(self, name: str, value: str) -> Any:
        ...

    async def setex(self, name: str, time: int, value: str) -> Any:
        ...

    async def get(self, name: str) -> str | None:
        ...

    async def delete(self, *names: str) -> int:
        ...

    async def zadd(self, name: str, mapping: Mapping[str, float]) -> int:
        ...

    async def zrem(self, name: str, *values: str) -> int:
        ...

    async def zcard(self, name: str) -> int:
        ...

    async def zrevrange(self, name: str, start: int, end: int) -> list[str]:
        ...

    async def zincrby(self, name: str, amount: float, value: str) -> float:
        ...


class RedisStore:
    def __init__(self, client: RedisClient) -> None:
        self._client = client

    @classmethod
    def from_url(cls, redis_url: str) -> "RedisStore":
        client = cast(RedisClient, Redis.from_url(redis_url, decode_responses=True))
        return cls(client)

    async def add_proxy(self, pool: ProxyPool, proxy: ProxyEndpoint) -> ProxyEndpoint:
        stored_proxy = proxy.model_copy(update={"status": pool})
        await self._save_proxy(pool, stored_proxy)
        return stored_proxy

    async def save_proxy(self, pool: ProxyPool, proxy: ProxyEndpoint) -> ProxyEndpoint:
        stored_proxy = proxy.model_copy(update={"status": pool})
        await self._save_proxy(pool, stored_proxy)
        return stored_proxy

    async def get_proxy(self, proxy_id: str) -> ProxyEndpoint | None:
        located = await self._get_proxy_with_pool(proxy_id)
        if located is None:
            return None
        _, proxy = located
        return proxy

    async def remove_proxy(self, pool: ProxyPool, proxy_id: str) -> bool:
        removed_from_index = await self._client.zrem(pool_index_key(pool), proxy_id)
        removed_key = await self._client.delete(proxy_key(pool, proxy_id))
        if removed_from_index or removed_key:
            await self._client.delete(proxy_pool_key(proxy_id))
            return True
        return False

    async def delete_proxy(self, proxy_id: str) -> bool:
        located = await self._get_proxy_with_pool(proxy_id)
        if located is None:
            return False
        pool, _ = located
        return await self.remove_proxy(pool, proxy_id)

    async def find_proxy_pool(self, proxy_id: str) -> ProxyPool | None:
        located = await self._get_proxy_with_pool(proxy_id)
        if located is None:
            return None
        pool, _ = located
        return pool

    async def move_proxy(
        self,
        from_pool: ProxyPool,
        to_pool: ProxyPool,
        proxy_id: str,
    ) -> ProxyEndpoint | None:
        payload = await self._client.get(proxy_key(from_pool, proxy_id))
        if payload is None:
            return None

        proxy = deserialize_proxy(payload).model_copy(update={"status": to_pool})
        await self._client.delete(proxy_key(from_pool, proxy_id))
        await self._client.zrem(pool_index_key(from_pool), proxy_id)
        await self._save_proxy(to_pool, proxy)
        return proxy

    async def list_proxies(
        self,
        pool: ProxyPool,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ProxyEndpoint]:
        if limit <= 0:
            return []

        start = max(offset, 0)
        stop = start + limit - 1
        proxy_ids = await self._client.zrevrange(pool_index_key(pool), start, stop)
        proxies: list[ProxyEndpoint] = []
        for proxy_id in proxy_ids:
            payload = await self._client.get(proxy_key(pool, proxy_id))
            if payload is not None:
                proxies.append(deserialize_proxy(payload))
        return proxies

    async def get_best_proxy(self, filters: ProxyFilters | None = None) -> ProxyEndpoint | None:
        active_filters = filters or ProxyFilters()
        for pool in SELECTION_POOLS:
            candidates = await self.list_proxies(pool)
            for proxy in candidates:
                if self._matches_filters(proxy, active_filters):
                    return proxy
        return None

    async def bind_session_proxy(
        self,
        session_id: str,
        proxy_id: str,
        ttl_seconds: int,
    ) -> None:
        await self._client.setex(session_proxy_key(session_id), ttl_seconds, proxy_id)

    async def get_session_proxy_id(self, session_id: str) -> str | None:
        return await self._client.get(session_proxy_key(session_id))

    async def update_score(self, proxy_id: str, score_delta: int) -> ProxyEndpoint | None:
        located = await self._get_proxy_with_pool(proxy_id)
        if located is None:
            return None

        pool, proxy = located
        updated_proxy = proxy.model_copy(update={"score": proxy.score + score_delta})
        await self._client.zincrby(pool_index_key(pool), float(score_delta), proxy_id)
        await self._client.set(proxy_key(pool, proxy_id), serialize_proxy(updated_proxy))
        return updated_proxy

    async def count_by_pool(self) -> dict[ProxyPool, int]:
        counts: dict[ProxyPool, int] = {}
        for pool in POOL_NAMES:
            counts[pool] = await self._client.zcard(pool_index_key(pool))
        return counts

    async def _save_proxy(self, pool: ProxyPool, proxy: ProxyEndpoint) -> None:
        await self._client.set(proxy_key(pool, proxy.id), serialize_proxy(proxy))
        await self._client.set(proxy_pool_key(proxy.id), pool)
        await self._client.zadd(pool_index_key(pool), {proxy.id: float(proxy.score)})

    async def _get_proxy_with_pool(self, proxy_id: str) -> tuple[ProxyPool, ProxyEndpoint] | None:
        pool = await self._get_recorded_pool(proxy_id)
        if pool is not None:
            payload = await self._client.get(proxy_key(pool, proxy_id))
            if payload is not None:
                return pool, deserialize_proxy(payload)

        for fallback_pool in POOL_NAMES:
            payload = await self._client.get(proxy_key(fallback_pool, proxy_id))
            if payload is not None:
                return fallback_pool, deserialize_proxy(payload)
        return None

    async def _get_recorded_pool(self, proxy_id: str) -> ProxyPool | None:
        pool = await self._client.get(proxy_pool_key(proxy_id))
        if pool in POOL_NAMES:
            return cast(ProxyPool, pool)
        return None

    @staticmethod
    def _matches_filters(proxy: ProxyEndpoint, filters: ProxyFilters) -> bool:
        if filters.scheme is not None and proxy.scheme != filters.scheme:
            return False
        if filters.anonymity is not None and proxy.anonymity != filters.anonymity:
            return False
        if filters.country is not None and proxy.country != filters.country:
            return False
        return not (filters.min_score is not None and proxy.score < filters.min_score)
