import asyncio

from fastapi.testclient import TestClient

from app.main import create_app
from app.models.proxy import ProxyEndpoint
from app.storage.redis_store import RedisStore
from tests.fakes import FakeRedis


def test_dashboard_renders_counts_sources_and_delete_action() -> None:
    app = create_app()
    store = RedisStore(FakeRedis())
    app.state.store = store
    proxy = ProxyEndpoint(
        id="http-1.2.3.4-8080",
        scheme="http",
        host="1.2.3.4",
        port=8080,
        username="user",
        password="secret",
        source="static",
        country="US",
        anonymity="elite",
        latency_ms=90,
        success_count=3,
        fail_count=1,
        score=95,
    )
    asyncio.run(store.add_proxy("elite", proxy))
    client = TestClient(app)

    response = client.get("/dashboard")

    assert response.status_code == 200
    assert "ProxyPool Architect" in response.text
    assert "static" in response.text
    assert "http-1.2.3.4-8080" in response.text
    assert 'data-delete-id="http-1.2.3.4-8080"' in response.text
    assert "secret" not in response.text
