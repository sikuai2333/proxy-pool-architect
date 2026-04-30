from collections.abc import Mapping

import pytest

from app.models.proxy import ProxyEndpoint, ProxyFilters
from app.storage.redis_store import RedisStore


class FakeRedis:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}
        self.sorted_sets: dict[str, dict[str, float]] = {}

    async def set(self, name: str, value: str) -> bool:
        self.values[name] = value
        return True

    async def get(self, name: str) -> str | None:
        return self.values.get(name)

    async def delete(self, *names: str) -> int:
        removed = 0
        for name in names:
            if name in self.values:
                removed += 1
                del self.values[name]
        return removed

    async def zadd(self, name: str, mapping: Mapping[str, float]) -> int:
        sorted_set = self.sorted_sets.setdefault(name, {})
        added = 0
        for member, score in mapping.items():
            if member not in sorted_set:
                added += 1
            sorted_set[member] = score
        return added

    async def zrem(self, name: str, *values: str) -> int:
        sorted_set = self.sorted_sets.setdefault(name, {})
        removed = 0
        for value in values:
            if value in sorted_set:
                removed += 1
                del sorted_set[value]
        return removed

    async def zcard(self, name: str) -> int:
        return len(self.sorted_sets.get(name, {}))

    async def zrevrange(self, name: str, start: int, end: int) -> list[str]:
        sorted_set = self.sorted_sets.get(name, {})
        members = sorted(sorted_set, key=lambda member: (-sorted_set[member], member))
        stop = None if end == -1 else end + 1
        return members[start:stop]

    async def zincrby(self, name: str, amount: float, value: str) -> float:
        sorted_set = self.sorted_sets.setdefault(name, {})
        sorted_set[value] = sorted_set.get(value, 0.0) + amount
        return sorted_set[value]


def make_proxy(proxy_id: str, score: int = 0, country: str | None = None) -> ProxyEndpoint:
    return ProxyEndpoint(
        id=proxy_id,
        scheme="http",
        host="127.0.0.1",
        port=8080,
        source="test",
        country=country,
        score=score,
    )


@pytest.fixture
def store() -> RedisStore:
    return RedisStore(FakeRedis())


async def test_add_get_list_and_count_by_pool(store: RedisStore) -> None:
    low_score = make_proxy("http-127.0.0.1-8080", score=10)
    high_score = make_proxy("http-127.0.0.1-8081", score=50)

    await store.add_proxy("raw", low_score)
    await store.add_proxy("raw", high_score)

    stored = await store.get_proxy(low_score.id)
    listed = await store.list_proxies("raw", limit=10, offset=0)
    counts = await store.count_by_pool()

    assert stored == low_score
    assert [proxy.id for proxy in listed] == [high_score.id, low_score.id]
    assert counts == {"raw": 2, "checked": 0, "elite": 0, "dead": 0}


async def test_move_proxy_updates_pool_and_indexes(store: RedisStore) -> None:
    proxy = make_proxy("http-127.0.0.1-8080", score=25)
    await store.add_proxy("raw", proxy)

    moved = await store.move_proxy("raw", "checked", proxy.id)

    assert moved is not None
    assert moved.status == "checked"
    assert await store.list_proxies("raw") == []
    assert await store.list_proxies("checked") == [moved]


async def test_remove_proxy_deletes_missing_keys_gracefully(store: RedisStore) -> None:
    proxy = make_proxy("http-127.0.0.1-8080")
    await store.add_proxy("dead", proxy)

    assert await store.remove_proxy("dead", proxy.id) is True
    assert await store.remove_proxy("dead", proxy.id) is False
    assert await store.get_proxy(proxy.id) is None


async def test_get_best_proxy_prefers_elite_then_checked_and_applies_filters(
    store: RedisStore,
) -> None:
    checked = make_proxy("http-127.0.0.1-8080", score=90, country="US")
    elite_low = make_proxy("http-127.0.0.1-8081", score=60, country="US").model_copy(
        update={"anonymity": "elite"}
    )
    elite_high = make_proxy("http-127.0.0.1-8082", score=80, country="SG").model_copy(
        update={"anonymity": "elite"}
    )

    stored_checked = await store.add_proxy("checked", checked)
    await store.add_proxy("elite", elite_low)
    stored_elite_high = await store.add_proxy("elite", elite_high)

    assert await store.get_best_proxy() == stored_elite_high
    assert await store.get_best_proxy(ProxyFilters(country="US", min_score=70)) == stored_checked
    assert await store.get_best_proxy(ProxyFilters(country="CN")) is None


async def test_update_score_changes_payload_and_sorted_index(store: RedisStore) -> None:
    first = make_proxy("http-127.0.0.1-8080", score=10)
    second = make_proxy("http-127.0.0.1-8081", score=20)
    await store.add_proxy("checked", first)
    await store.add_proxy("checked", second)

    updated = await store.update_score(first.id, 30)
    listed = await store.list_proxies("checked")

    assert updated is not None
    assert updated.score == 40
    assert [proxy.id for proxy in listed] == [first.id, second.id]
    assert await store.update_score("missing", 10) is None
