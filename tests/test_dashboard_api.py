import asyncio

from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.core.scheduler import SchedulerService
from app.main import create_app
from app.models.dashboard import ValidationJob
from app.models.provider import ProviderFetchResult
from app.models.proxy import ProxyEndpoint
from app.services.url_import_service import ProxyUrlImportService
from app.storage.redis_store import RedisStore
from app.utils.time import utc_now_iso
from tests.fakes import FakeRedis


def make_proxy(
    proxy_id: str,
    *,
    source: str = "static",
    status: str = "checked",
    country: str | None = "US",
    asn: str | None = "AS64500",
    latency_ms: int | None = 120,
) -> ProxyEndpoint:
    return ProxyEndpoint(
        id=proxy_id,
        scheme="http",
        host=proxy_id.split("-")[1],
        port=8080,
        source=source,
        country=country,
        asn=asn,
        anonymity="elite",
        latency_ms=latency_ms,
        success_count=4,
        fail_count=1,
        score=90,
        status=status,
    )


def make_client() -> tuple[TestClient, RedisStore]:
    app = create_app()
    store = RedisStore(FakeRedis())
    app.state.store = store
    return TestClient(app), store


def restore_settings(snapshot) -> None:
    settings = get_settings()
    for field, value in snapshot.model_dump().items():
        setattr(settings, field, value)


def test_dashboard_geo_and_provider_endpoints_return_live_summaries() -> None:
    client, store = make_client()
    asyncio.run(store.add_proxy("checked", make_proxy("http-1.2.3.4-8080", status="checked")))
    asyncio.run(store.add_proxy("elite", make_proxy("http-5.6.7.8-8080", status="elite")))
    asyncio.run(
        store.add_proxy(
            "dead",
            make_proxy(
                "http-9.9.9.9-8080",
                status="dead",
                country="SG",
                asn="AS15169",
                latency_ms=240,
            ),
        )
    )
    client.app.state.runtime_activity.record_provider_fetch_results(
        [ProviderFetchResult(name="static", enabled=True, fetched_count=3)],
        fetched_at="2026-05-01T08:00:00+08:00",
    )

    providers_response = client.get("/providers")
    provider_response = client.get("/providers/static")
    geo_response = client.get("/geo/summary")

    assert providers_response.status_code == 200
    providers = providers_response.json()["items"]
    assert providers[0]["name"] == "static"
    assert providers[0]["enabled"] is True
    assert providers[0]["fetched_count"] == 3
    assert providers[0]["valid_count"] == 2
    assert providers[0]["last_fetch_at"] == "2026-05-01T08:00:00+08:00"

    assert provider_response.status_code == 200
    assert provider_response.json()["name"] == "static"

    assert geo_response.status_code == 200
    geo_payload = geo_response.json()
    assert geo_payload["coverage"] == {
        "total_proxies": 3,
        "geo_tagged_proxies": 3,
        "unresolved_proxies": 0,
        "geo_enabled": False,
        "geo_file": "config/geo.csv",
        "geo_file_exists": False,
    }
    assert geo_payload["countries"][0]["country"] == "US"
    assert geo_payload["countries"][0]["total"] == 2
    assert geo_payload["asns"][0]["asn"] == "AS64500"


def test_dashboard_events_validation_jobs_and_settings_endpoints_roundtrip() -> None:
    client, _ = make_client()
    settings = get_settings()
    original = settings.model_copy(deep=True)
    now = utc_now_iso()
    client.app.state.runtime_activity.record_event(
        "validation_failed",
        "warning",
        "Proxy timed out during validation.",
        created_at=now,
    )
    client.app.state.runtime_activity.record_validation_job(
        ValidationJob(
            id="job-001",
            started_at=now,
            finished_at=now,
            checked_count=12,
            success_count=5,
            fail_count=7,
            timeout_count=2,
            status="finished",
        )
    )

    try:
        settings_response = client.get("/settings")
        patch_response = client.patch(
            "/settings",
            json={
                "fetch_interval_seconds": 900,
                "validate_interval_seconds": 300,
                "validate_timeout_seconds": 5,
                "validate_concurrency": 42,
                "min_elite_score": 88,
                "cooldown_seconds": 1200,
                "safe_networking": {
                    "authorized_targets_only": True,
                    "block_private_networks": True,
                    "mask_proxy_credentials": True,
                },
            },
        )
        events_response = client.get("/events?limit=10&offset=0")
        jobs_response = client.get("/validation/jobs?limit=10&offset=0")

        assert settings_response.status_code == 200
        assert settings_response.json()["validate_concurrency"] == original.validate_concurrency

        assert patch_response.status_code == 200
        patched = patch_response.json()
        assert patched["validate_concurrency"] == 42
        assert patched["fetch_interval_seconds"] == 900

        assert jobs_response.status_code == 200
        assert jobs_response.json()["items"][0]["id"] == "job-001"
        assert jobs_response.json()["total"] == 1
        assert jobs_response.json()["limit"] == 10
        assert jobs_response.json()["offset"] == 0

        assert events_response.status_code == 200
        event_types = [item["type"] for item in events_response.json()["items"]]
        assert events_response.json()["total"] == 2
        assert "settings_updated" in event_types
        assert "validation_failed" in event_types
    finally:
        restore_settings(original)


def test_dashboard_event_and_validation_pagination() -> None:
    client, _ = make_client()
    now = utc_now_iso()
    client.app.state.runtime_activity.record_event(
        "event-1",
        "info",
        "first",
        created_at=now,
    )
    client.app.state.runtime_activity.record_event(
        "event-2",
        "warning",
        "second",
        created_at=now,
    )
    client.app.state.runtime_activity.record_validation_job(
        ValidationJob(
            id="job-001",
            started_at=now,
            finished_at=now,
            checked_count=10,
            success_count=2,
            fail_count=8,
            timeout_count=1,
            status="finished",
        )
    )
    client.app.state.runtime_activity.record_validation_job(
        ValidationJob(
            id="job-002",
            started_at=now,
            finished_at=now,
            checked_count=5,
            success_count=1,
            fail_count=4,
            timeout_count=0,
            status="finished",
        )
    )

    events_response = client.get("/events?limit=1&offset=1")
    jobs_response = client.get("/validation/jobs?limit=1&offset=1")

    assert events_response.status_code == 200
    assert events_response.json()["total"] == 2
    assert events_response.json()["items"][0]["type"] == "event-1"

    assert jobs_response.status_code == 200
    assert jobs_response.json()["total"] == 2
    assert jobs_response.json()["items"][0]["id"] == "job-001"


def test_dashboard_provider_import_url_endpoint_stores_proxies_and_updates_summary(
    monkeypatch,
) -> None:
    client, store = make_client()

    async def fake_download(self, url: str) -> str:
        assert url == "https://example.com/http.txt"
        return "1.2.3.4:8080\n1.2.3.4:8080\nbad-entry\n"

    monkeypatch.setattr(ProxyUrlImportService, "_download_text", fake_download)

    response = client.post(
        "/providers/import-url",
        json={"url": "https://example.com/http.txt", "file_type": "http"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload == {
        "source": "url_submit:http:example.com:http.txt",
        "file_type": "http",
        "detected_format": "plain_text",
        "fetched_count": 3,
        "valid_count": 2,
        "stored_count": 1,
        "duplicate_count": 1,
        "invalid_count": 1,
        "direct_supported_count": 2,
        "adapter_required_count": 0,
        "unsupported_count": 0,
        "detected_protocols": ["http"],
        "supported_connection_modes": ["direct"],
    }
    assert [proxy.id for proxy in asyncio.run(store.list_proxies("raw", limit=10, offset=0))] == [
        "http-1.2.3.4-8080"
    ]

    providers_response = client.get("/providers")
    providers = providers_response.json()["items"]
    imported = next(
        item for item in providers if item["name"] == "url_submit:http:example.com:http.txt"
    )
    assert imported["fetched_count"] == 2
    assert imported["enabled"] is True


def test_dashboard_validation_run_endpoint_returns_manual_job(monkeypatch) -> None:
    client, _ = make_client()

    async def fake_run(self, limit: int | None = None) -> ValidationJob:
        assert limit == 25
        return ValidationJob(
            id="job-manual-001",
            started_at="2026-05-01T08:00:00+08:00",
            finished_at="2026-05-01T08:00:05+08:00",
            checked_count=25,
            success_count=3,
            fail_count=22,
            timeout_count=10,
            status="finished",
        )

    monkeypatch.setattr(SchedulerService, "run_validate_once", fake_run)

    response = client.post("/validation/run?limit=25")

    assert response.status_code == 200
    assert response.json() == {
        "id": "job-manual-001",
        "started_at": "2026-05-01T08:00:00+08:00",
        "finished_at": "2026-05-01T08:00:05+08:00",
        "checked_count": 25,
        "success_count": 3,
        "fail_count": 22,
        "timeout_count": 10,
        "status": "finished",
    }
