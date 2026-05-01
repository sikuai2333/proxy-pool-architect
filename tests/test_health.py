from fastapi.testclient import TestClient

from app.main import create_app


def test_health_endpoint_returns_ok() -> None:
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["app"] == "ProxyPool Architect"
    assert payload["version"] == "0.1.0"
    assert payload["redis_configured"] is True
    assert payload["redis"] == "ok"
    assert payload["scheduler"] == "stopped"


def test_health_endpoint_allows_dashboard_dev_origin() -> None:
    client = TestClient(create_app())

    response = client.get("/health", headers={"Origin": "http://localhost:5173"})

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
