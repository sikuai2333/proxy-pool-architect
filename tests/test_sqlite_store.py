import pytest

from app.models.proxy import ProxyEndpoint, ProxyFilters
from app.storage.sqlite_store import SQLiteStore


def make_proxy(
    proxy_id: str,
    score: int = 0,
    country: str | None = None,
    source: str = "test",
) -> ProxyEndpoint:
    return ProxyEndpoint(
        id=proxy_id,
        scheme="http",
        host="127.0.0.1",
        port=8080,
        source=source,
        country=country,
        score=score,
    )


@pytest.fixture
def store() -> SQLiteStore:
    return SQLiteStore(":memory:")


async def test_add_get_list_and_count_by_pool(store: SQLiteStore) -> None:
    low_score = make_proxy("http-127.0.0.1-8080", score=10)
    high_score = make_proxy("http-127.0.0.1-8081", score=50)

    await store.add_proxy("raw", low_score)
    await store.add_proxy("raw", high_score)

    stored = await store.get_proxy(low_score.id)
    listed = await store.list_proxies("raw", limit=10, offset=0)
    counts = await store.count_by_pool()

    assert stored == low_score
    assert [proxy.id for proxy in listed] == [high_score.id, low_score.id]
    assert counts == {"raw": 2, "checked": 0, "elite": 0, "dead": 0, "cooldown": 0}


async def test_move_proxy_updates_pool_and_indexes(store: SQLiteStore) -> None:
    proxy = make_proxy("http-127.0.0.1-8080", score=25)
    await store.add_proxy("raw", proxy)

    moved = await store.move_proxy("raw", "checked", proxy.id)

    assert moved is not None
    assert moved.status == "checked"
    assert await store.list_proxies("raw") == []
    assert await store.list_proxies("checked") == [moved]


async def test_remove_proxy_deletes_missing_keys_gracefully(store: SQLiteStore) -> None:
    proxy = make_proxy("http-127.0.0.1-8080")
    await store.add_proxy("dead", proxy)

    assert await store.remove_proxy("dead", proxy.id) is True
    assert await store.remove_proxy("dead", proxy.id) is False
    assert await store.get_proxy(proxy.id) is None


async def test_get_best_proxy_prefers_elite_then_checked_and_applies_filters(
    store: SQLiteStore,
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


async def test_update_score_changes_payload_and_sorted_index(store: SQLiteStore) -> None:
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


async def test_filtered_proxy_list_applies_country_and_source_filters(
    store: SQLiteStore,
) -> None:
    first = make_proxy("http-127.0.0.1-8080", score=10, source="provider-a")
    second = make_proxy("http-127.0.0.2-8080", score=50, country="US", source="provider-b")
    third = make_proxy("http-127.0.0.3-8080", score=70, country="US", source="provider-b")
    await store.add_proxy("checked", first)
    await store.add_proxy("checked", second)
    await store.add_proxy("elite", third)

    page, total = await store.list_filtered_proxies(
        pool=None,
        filters=ProxyFilters(country="US", source="provider-b"),
        limit=1,
        offset=0,
    )

    assert total == 2
    assert [proxy.id for proxy in page] == [third.id]

    await store.delete_proxy(third.id)

    page_after_delete, total_after_delete = await store.list_filtered_proxies(
        pool=None,
        filters=ProxyFilters(country="US", source="provider-b"),
        limit=10,
        offset=0,
    )

    assert total_after_delete == 1
    assert [proxy.id for proxy in page_after_delete] == [second.id]


async def test_filtered_proxy_list_supports_min_score_pagination(store: SQLiteStore) -> None:
    first = make_proxy("http-127.0.0.1-8080", score=10)
    second = make_proxy("http-127.0.0.2-8080", score=30)
    third = make_proxy("http-127.0.0.3-8080", score=20)
    await store.add_proxy("checked", first)
    await store.add_proxy("checked", second)
    await store.add_proxy("raw", third)

    page, total = await store.list_filtered_proxies(
        pool=None,
        filters=ProxyFilters(min_score=15),
        limit=1,
        offset=1,
    )

    assert total == 2
    assert [proxy.id for proxy in page] == [third.id]


async def test_save_proxy_updates_attribute_indexes(store: SQLiteStore) -> None:
    proxy = make_proxy("http-127.0.0.1-8080", score=20, source="provider-a")
    await store.add_proxy("checked", proxy)

    await store.save_proxy("checked", proxy.model_copy(update={"source": "provider-b"}))

    old_items, old_total = await store.list_filtered_proxies(
        pool="checked",
        filters=ProxyFilters(source="provider-a"),
        limit=10,
        offset=0,
    )
    new_items, new_total = await store.list_filtered_proxies(
        pool="checked",
        filters=ProxyFilters(source="provider-b"),
        limit=10,
        offset=0,
    )

    assert old_items == []
    assert old_total == 0
    assert new_total == 1
    assert new_items[0].source == "provider-b"


async def test_session_affinity_binding_round_trips_proxy_id(store: SQLiteStore) -> None:
    await store.bind_session_proxy("task-1", "http-127.0.0.1-8080", ttl_seconds=60)

    assert await store.get_session_proxy_id("task-1") == "http-127.0.0.1-8080"
    assert await store.get_session_proxy_id("missing") is None
