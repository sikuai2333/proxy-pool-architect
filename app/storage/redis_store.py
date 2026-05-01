from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from collections.abc import Set as AbstractSet
from typing import Any, Protocol, cast

from redis.asyncio import Redis

from app.models.proxy import ProxyEndpoint, ProxyFilters, ProxyPool
from app.storage.keys import (
    POOL_NAMES,
    SELECTION_POOLS,
    admin_session_key,
    all_proxy_index_key,
    pool_index_key,
    proxy_attribute_index_key,
    proxy_key,
    proxy_list_cache_index_key,
    proxy_list_cache_key,
    proxy_pool_key,
    session_proxy_key,
)
from app.storage.serializers import deserialize_proxy, serialize_proxy

DEFAULT_LIST_CACHE_TTL_SECONDS = 10


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

    async def zcount(self, name: str, min: float | str, max: float | str) -> int:
        ...

    async def zrevrange(self, name: str, start: int, end: int) -> list[str]:
        ...

    async def zrevrangebyscore(
        self,
        name: str,
        max: float | str,
        min: float | str,
        start: int | None = None,
        num: int | None = None,
    ) -> list[str]:
        ...

    async def zincrby(self, name: str, amount: float, value: str) -> float:
        ...

    async def sadd(self, name: str, *values: str) -> int:
        ...

    async def smembers(self, name: str) -> AbstractSet[str]:
        ...


class RedisStore:
    def __init__(
        self,
        client: RedisClient,
        list_cache_ttl_seconds: int = DEFAULT_LIST_CACHE_TTL_SECONDS,
    ) -> None:
        self._client = client
        self._list_cache_ttl_seconds = max(list_cache_ttl_seconds, 0)

    @classmethod
    def from_url(
        cls,
        redis_url: str,
        list_cache_ttl_seconds: int = DEFAULT_LIST_CACHE_TTL_SECONDS,
    ) -> RedisStore:
        client = cast(RedisClient, Redis.from_url(redis_url, decode_responses=True))
        return cls(client, list_cache_ttl_seconds=list_cache_ttl_seconds)

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
        payload = await self._client.get(proxy_key(pool, proxy_id))
        if payload is not None:
            await self._remove_proxy_indexes(pool, deserialize_proxy(payload))
        removed_from_index = await self._client.zrem(pool_index_key(pool), proxy_id)
        removed_key = await self._client.delete(proxy_key(pool, proxy_id))
        if removed_from_index or removed_key:
            await self._client.delete(proxy_pool_key(proxy_id))
            await self._clear_list_cache()
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

    async def get_proxy_record(self, proxy_id: str) -> tuple[ProxyPool, ProxyEndpoint] | None:
        return await self._get_proxy_with_pool(proxy_id)

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
        await self.remove_proxy(from_pool, proxy_id)
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
        await self._ensure_secondary_indexes()
        active_filters = filters or ProxyFilters()
        for pool in SELECTION_POOLS:
            candidates, _ = await self.list_filtered_proxies(
                pool=pool,
                filters=active_filters,
                limit=1,
                offset=0,
            )
            if candidates:
                return candidates[0]
        return None

    async def list_filtered_proxies(
        self,
        pool: ProxyPool | None,
        filters: ProxyFilters | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[ProxyEndpoint], int]:
        active_filters = filters or ProxyFilters()
        if limit <= 0:
            return [], 0
        await self._ensure_secondary_indexes()

        cached = await self._get_cached_proxy_list(pool, active_filters, limit, offset)
        if cached is not None:
            return cached

        proxies, total = await self._list_filtered_proxies_uncached(
            pool=pool,
            filters=active_filters,
            limit=limit,
            offset=max(offset, 0),
        )
        await self._cache_proxy_list(pool, active_filters, limit, offset, proxies, total)
        return proxies, total

    async def bind_session_proxy(
        self,
        session_id: str,
        proxy_id: str,
        ttl_seconds: int,
    ) -> None:
        await self._client.setex(session_proxy_key(session_id), ttl_seconds, proxy_id)

    async def get_session_proxy_id(self, session_id: str) -> str | None:
        return await self._client.get(session_proxy_key(session_id))

    async def save_admin_session(self, token: str, payload: str, ttl_seconds: int) -> None:
        await self._client.setex(admin_session_key(token), ttl_seconds, payload)

    async def get_admin_session(self, token: str) -> str | None:
        return await self._client.get(admin_session_key(token))

    async def delete_admin_session(self, token: str) -> bool:
        return bool(await self._client.delete(admin_session_key(token)))

    async def update_score(self, proxy_id: str, score_delta: int) -> ProxyEndpoint | None:
        located = await self._get_proxy_with_pool(proxy_id)
        if located is None:
            return None

        pool, proxy = located
        updated_proxy = proxy.model_copy(update={"score": proxy.score + score_delta})
        await self._save_proxy(pool, updated_proxy)
        return updated_proxy

    async def count_by_pool(self) -> dict[ProxyPool, int]:
        counts: dict[ProxyPool, int] = {}
        for pool in POOL_NAMES:
            counts[pool] = await self._client.zcard(pool_index_key(pool))
        return counts

    async def list_all_proxies(self) -> list[ProxyEndpoint]:
        counts = await self.count_by_pool()
        proxies: list[ProxyEndpoint] = []
        for pool in POOL_NAMES:
            total = counts.get(pool, 0)
            if total <= 0:
                continue
            proxies.extend(await self.list_proxies(pool, limit=total, offset=0))
        return proxies

    async def _save_proxy(self, pool: ProxyPool, proxy: ProxyEndpoint) -> None:
        located = await self._get_proxy_with_pool(proxy.id)
        if located is not None:
            previous_pool, previous_proxy = located
            await self._remove_proxy_indexes(previous_pool, previous_proxy)
            if previous_pool != pool:
                await self._client.delete(proxy_key(previous_pool, proxy.id))

        await self._client.set(proxy_key(pool, proxy.id), serialize_proxy(proxy))
        await self._client.set(proxy_pool_key(proxy.id), pool)
        await self._client.zadd(pool_index_key(pool), {proxy.id: float(proxy.score)})
        await self._client.zadd(all_proxy_index_key(), {proxy.id: float(proxy.score)})
        for index_key in self._proxy_attribute_index_keys(proxy):
            await self._client.zadd(index_key, {proxy.id: float(proxy.score)})
        await self._clear_list_cache()

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

    async def _ensure_secondary_indexes(self) -> None:
        if await self._client.zcard(all_proxy_index_key()) > 0:
            return

        counts = await self.count_by_pool()
        if sum(counts.values()) == 0:
            return

        for pool in POOL_NAMES:
            proxy_ids = await self._client.zrevrange(pool_index_key(pool), 0, -1)
            for proxy_id in proxy_ids:
                payload = await self._client.get(proxy_key(pool, proxy_id))
                if payload is None:
                    continue
                proxy = deserialize_proxy(payload)
                await self._client.zadd(all_proxy_index_key(), {proxy.id: float(proxy.score)})
                for index_key in self._proxy_attribute_index_keys(proxy):
                    await self._client.zadd(index_key, {proxy.id: float(proxy.score)})

    async def _list_filtered_proxies_uncached(
        self,
        pool: ProxyPool | None,
        filters: ProxyFilters,
        limit: int,
        offset: int,
    ) -> tuple[list[ProxyEndpoint], int]:
        base_key = pool_index_key(pool) if pool is not None else all_proxy_index_key()
        exact_index_keys = self._filter_index_keys(filters)

        if not exact_index_keys and not self._has_query_filter(filters):
            total, proxy_ids = await self._list_page_from_score_index(
                key=base_key,
                min_score=filters.min_score,
                limit=limit,
                offset=offset,
            )
            return await self._load_proxy_ids(proxy_ids, known_pool=pool), total

        candidate_keys = [base_key, *exact_index_keys]
        candidate_ids = await self._intersect_sorted_set_members(candidate_keys)
        proxies = await self._load_proxy_ids(candidate_ids, known_pool=pool)
        filtered = [proxy for proxy in proxies if self._matches_filters(proxy, filters)]
        filtered.sort(key=lambda item: (-item.score, item.id))
        total = len(filtered)
        return filtered[offset : offset + limit], total

    async def _list_page_from_score_index(
        self,
        key: str,
        min_score: int | None,
        limit: int,
        offset: int,
    ) -> tuple[int, list[str]]:
        if min_score is None:
            total = await self._client.zcard(key)
            proxy_ids = await self._client.zrevrange(key, offset, offset + limit - 1)
            return total, proxy_ids

        total = await self._client.zcount(key, float(min_score), "+inf")
        proxy_ids = await self._client.zrevrangebyscore(
            key,
            "+inf",
            float(min_score),
            start=offset,
            num=limit,
        )
        return total, proxy_ids

    async def _intersect_sorted_set_members(self, keys: list[str]) -> list[str]:
        if not keys:
            return []

        member_sets = [set(await self._client.zrevrange(key, 0, -1)) for key in keys]
        if not member_sets:
            return []

        member_sets.sort(key=len)
        intersection = set(member_sets[0])
        for members in member_sets[1:]:
            intersection.intersection_update(members)
            if not intersection:
                return []
        return list(intersection)

    async def _load_proxy_ids(
        self,
        proxy_ids: list[str],
        known_pool: ProxyPool | None = None,
    ) -> list[ProxyEndpoint]:
        proxies: list[ProxyEndpoint] = []
        for proxy_id in proxy_ids:
            if known_pool is not None:
                payload = await self._client.get(proxy_key(known_pool, proxy_id))
                if payload is not None:
                    proxies.append(deserialize_proxy(payload))
                continue

            proxy = await self.get_proxy(proxy_id)
            if proxy is not None:
                proxies.append(proxy)
        return proxies

    async def _get_cached_proxy_list(
        self,
        pool: ProxyPool | None,
        filters: ProxyFilters,
        limit: int,
        offset: int,
    ) -> tuple[list[ProxyEndpoint], int] | None:
        if self._list_cache_ttl_seconds <= 0:
            return None

        payload = await self._client.get(
            proxy_list_cache_key(self._list_cache_signature(pool, filters, limit, offset))
        )
        if payload is None:
            return None

        raw = json.loads(payload)
        proxies = [ProxyEndpoint.model_validate(item) for item in raw["items"]]
        return proxies, int(raw["total"])

    async def _cache_proxy_list(
        self,
        pool: ProxyPool | None,
        filters: ProxyFilters,
        limit: int,
        offset: int,
        proxies: list[ProxyEndpoint],
        total: int,
    ) -> None:
        if self._list_cache_ttl_seconds <= 0:
            return

        cache_key = proxy_list_cache_key(self._list_cache_signature(pool, filters, limit, offset))
        payload = json.dumps(
            {
                "items": [proxy.model_dump(mode="json") for proxy in proxies],
                "total": total,
            },
            separators=(",", ":"),
            sort_keys=True,
        )
        await self._client.setex(cache_key, self._list_cache_ttl_seconds, payload)
        await self._client.sadd(proxy_list_cache_index_key(), cache_key)

    async def _clear_list_cache(self) -> None:
        cache_keys = await self._client.smembers(proxy_list_cache_index_key())
        if cache_keys:
            await self._client.delete(*cache_keys)
        await self._client.delete(proxy_list_cache_index_key())

    @staticmethod
    def _list_cache_signature(
        pool: ProxyPool | None,
        filters: ProxyFilters,
        limit: int,
        offset: int,
    ) -> str:
        payload = json.dumps(
            {
                "pool": pool,
                "filters": filters.model_dump(mode="json", exclude_none=True),
                "limit": limit,
                "offset": offset,
            },
            separators=(",", ":"),
            sort_keys=True,
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    @staticmethod
    def _filter_index_keys(filters: ProxyFilters) -> list[str]:
        keys: list[str] = []
        if filters.scheme is not None:
            keys.append(proxy_attribute_index_key("scheme", filters.scheme))
        if filters.anonymity is not None:
            keys.append(proxy_attribute_index_key("anonymity", filters.anonymity))
        if filters.country:
            keys.append(proxy_attribute_index_key("country", filters.country))
        if filters.source:
            keys.append(proxy_attribute_index_key("source", filters.source))
        return keys

    @staticmethod
    def _has_query_filter(filters: ProxyFilters) -> bool:
        return filters.query is not None and bool(filters.query.strip())

    @staticmethod
    def _proxy_attribute_index_keys(proxy: ProxyEndpoint) -> list[str]:
        keys = [
            proxy_attribute_index_key("scheme", proxy.scheme),
            proxy_attribute_index_key("anonymity", proxy.anonymity),
            proxy_attribute_index_key("source", proxy.source),
        ]
        if proxy.country:
            keys.append(proxy_attribute_index_key("country", proxy.country))
        return keys

    async def _remove_proxy_indexes(self, pool: ProxyPool, proxy: ProxyEndpoint) -> None:
        proxy_id = proxy.id
        await self._client.zrem(pool_index_key(pool), proxy_id)
        await self._client.zrem(all_proxy_index_key(), proxy_id)
        for index_key in self._proxy_attribute_index_keys(proxy):
            await self._client.zrem(index_key, proxy_id)

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
