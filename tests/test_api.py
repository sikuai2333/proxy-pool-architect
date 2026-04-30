import asyncio

from fastapi.testclient import TestClient

from app.main import create_app
from app.models.proxy import ProxyEndpoint
from app.storage.redis_store import RedisStore
from tests.fakes import FakeRedis


def make_proxy(
    proxy_id: str,
    score: int = 90,
    country: str | None = "US",
    username: str | None = None,
    password: str | None = None,
) -> ProxyEndpoint:
    return ProxyEndpoint(
        id=proxy_id,
        scheme="http",
        host="1.2.3.4",
        port=8080,
        username=username,
        password=password,
        source="test",
        country=country,
        anonymity="elite",
        latency_ms=120,
        success_count=2,
        fail_count=1,
        score=score,
    )


def make_client() -> tuple[TestClient, RedisStore]:
    app = create_app()
    store = RedisStore(FakeRedis())
    app.state.store = store
    return TestClient(app), store


def test_get_proxy_returns_best_proxy_without_password() -> None:
    client, store = make_client()
    proxy = make_proxy(
        "http-1.2.3.4-8080",
        username="user",
        password="secret",
    )
    asyncio.run(store.add_proxy("elite", proxy))

    response = client.get("/proxy")

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == proxy.id
    assert payload["auth_required"] is True
    assert "password" not in payload
    assert "username" not in payload


def test_get_proxy_supports_text_format_without_credentials() -> None:
    client, store = make_client()
    asyncio.run(
        store.add_proxy(
            "elite",
            make_proxy("http-1.2.3.4-8080", username="user", password="secret"),
        )
    )

    response = client.get("/proxy", params={"format": "text"})

    assert response.status_code == 200
    assert response.text == "http://1.2.3.4:8080"


def test_get_proxy_returns_404_when_no_proxy_matches() -> None:
    client, store = make_client()
    asyncio.run(store.add_proxy("checked", make_proxy("http-1.2.3.4-8080", country="US")))

    response = client.get("/proxy", params={"country": "SG"})

    assert response.status_code == 404


def test_list_proxies_filters_by_pool_and_country() -> None:
    client, store = make_client()
    asyncio.run(store.add_proxy("checked", make_proxy("http-1.2.3.4-8080", country="US")))
    asyncio.run(store.add_proxy("checked", make_proxy("http-1.2.3.5-8080", country="SG")))

    response = client.get("/proxy/list", params={"pool": "checked", "country": "US"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 1
    assert payload["proxies"][0]["id"] == "http-1.2.3.4-8080"


def test_report_proxy_updates_score_and_counts() -> None:
    client, store = make_client()
    asyncio.run(store.add_proxy("checked", make_proxy("http-1.2.3.4-8080", score=50)))

    response = client.post(
        "/proxy/report",
        json={"proxy_id": "http-1.2.3.4-8080", "ok": True, "latency_ms": 80},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["score"] == 60
    assert payload["success_count"] == 3


def test_report_proxy_moves_repeated_failure_to_cooldown() -> None:
    client, store = make_client()
    proxy = make_proxy("http-1.2.3.4-8080", score=50).model_copy(
        update={"fail_count": 2, "consecutive_fail_count": 2}
    )
    asyncio.run(store.add_proxy("checked", proxy))

    response = client.post(
        "/proxy/report",
        json={"proxy_id": "http-1.2.3.4-8080", "ok": False, "error": "timeout"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "cooldown"
    assert payload["fail_count"] == 3
    assert [stored.id for stored in asyncio.run(store.list_proxies("cooldown"))] == [
        "http-1.2.3.4-8080"
    ]


def test_stats_returns_pool_counts_and_rates() -> None:
    client, store = make_client()
    asyncio.run(store.add_proxy("checked", make_proxy("http-1.2.3.4-8080")))

    response = client.get("/stats")

    assert response.status_code == 200
    payload = response.json()
    assert payload["pools"]["checked"] == 1
    assert payload["total"] == 1
    assert payload["average_latency_ms"] == 120
    assert payload["success_rate"] == 2 / 3


def test_delete_proxy_removes_proxy() -> None:
    client, store = make_client()
    asyncio.run(store.add_proxy("checked", make_proxy("http-1.2.3.4-8080")))

    response = client.delete("/proxy/http-1.2.3.4-8080")

    assert response.status_code == 200
    assert response.json() == {"proxy_id": "http-1.2.3.4-8080", "deleted": True}
    assert asyncio.run(store.get_proxy("http-1.2.3.4-8080")) is None


def test_delete_proxy_returns_404_for_missing_proxy() -> None:
    client, _ = make_client()

    response = client.delete("/proxy/missing")

    assert response.status_code == 404
