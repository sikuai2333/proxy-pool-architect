import asyncio

from app.models.proxy import ProxyEndpoint
from app.services.metrics_service import MetricsService
from app.storage.redis_store import RedisStore
from tests.fakes import FakeRedis


def test_metrics_service_renders_prometheus_text() -> None:
    async def run() -> None:
        store = RedisStore(FakeRedis())
        await store.add_proxy(
            "checked",
            ProxyEndpoint(
                id="http-1.2.3.4-8080",
                scheme="http",
                host="1.2.3.4",
                port=8080,
                source='static"source',
                latency_ms=100,
                success_count=3,
                fail_count=1,
                score=80,
            ),
        )

        metrics = await MetricsService(store).render_prometheus()

        assert 'proxy_pool_proxies{pool="checked"} 1' in metrics
        assert "proxy_pool_total_proxies 1" in metrics
        assert "proxy_pool_average_latency_ms 100.0" in metrics
        assert "proxy_pool_success_rate 0.75" in metrics
        assert 'proxy_pool_source_proxies{source="static\\"source"} 1' in metrics

    asyncio.run(run())
