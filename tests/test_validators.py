import asyncio

import httpx

from app.models.proxy import ProxyEndpoint
from app.services.validate_service import ValidateService
from app.storage.redis_store import RedisStore
from app.validators.anonymity import AnonymityValidator
from app.validators.connectivity import ConnectivityValidator
from app.validators.protocol import ProtocolValidator
from tests.fakes import FakeRedis


def make_proxy(proxy_id: str = "http-1.2.3.4-8080") -> ProxyEndpoint:
    return ProxyEndpoint(
        id=proxy_id,
        scheme="http",
        host="1.2.3.4",
        port=8080,
        source="test",
    )


def test_protocol_validator_rejects_invalid_proxy() -> None:
    async def run() -> None:
        proxy = ProxyEndpoint.model_construct(
            id="invalid",
            scheme="ftp",
            host="",
            port=0,
            source="test",
        )

        result = await ProtocolValidator().validate(proxy)

        assert result.ok is False
        assert result.error == "unsupported_proxy_scheme"

    asyncio.run(run())


def test_connectivity_validator_returns_success() -> None:
    async def run() -> None:
        transport = httpx.MockTransport(
            lambda request: httpx.Response(200, json={"origin": "1.2.3.4"})
        )
        validator = ConnectivityValidator(
            test_url="https://example.test/ip",
            timeout_seconds=1,
            transport=transport,
        )

        result = await validator.validate(make_proxy())

        assert result.ok is True
        assert result.status_code == 200
        assert result.latency_ms is not None

    asyncio.run(run())


def test_connectivity_validator_handles_timeout() -> None:
    async def run() -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ReadTimeout("timeout", request=request)

        validator = ConnectivityValidator(
            test_url="https://example.test/ip",
            timeout_seconds=1,
            transport=httpx.MockTransport(handler),
        )

        result = await validator.validate(make_proxy())

        assert result.ok is False
        assert result.error == "timeout"

    asyncio.run(run())


def test_connectivity_validator_handles_connection_error() -> None:
    async def run() -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("connection failed", request=request)

        validator = ConnectivityValidator(
            test_url="https://example.test/ip",
            timeout_seconds=1,
            transport=httpx.MockTransport(handler),
        )

        result = await validator.validate(make_proxy())

        assert result.ok is False
        assert result.error == "ConnectError"

    asyncio.run(run())


def test_anonymity_validator_detects_transparent_proxy() -> None:
    async def run() -> None:
        transport = httpx.MockTransport(
            lambda request: httpx.Response(
                200,
                json={"headers": {"X-Forwarded-For": "10.0.0.1"}},
            )
        )
        validator = AnonymityValidator(
            test_url="https://example.test/headers",
            timeout_seconds=1,
            transport=transport,
        )

        result = await validator.validate(make_proxy())

        assert result.ok is True
        assert result.anonymity == "transparent"

    asyncio.run(run())


def test_anonymity_validator_marks_unstructured_response_as_anonymous() -> None:
    async def run() -> None:
        transport = httpx.MockTransport(lambda request: httpx.Response(200, text="ok"))
        validator = AnonymityValidator(
            test_url="https://example.test/headers",
            timeout_seconds=1,
            transport=transport,
        )

        result = await validator.validate(make_proxy())

        assert result.ok is True
        assert result.anonymity == "anonymous"

    asyncio.run(run())


def test_validate_service_moves_successful_elite_proxy_to_elite_pool() -> None:
    async def run() -> None:
        store = RedisStore(FakeRedis())
        proxy = await store.add_proxy("raw", make_proxy())
        connectivity_transport = httpx.MockTransport(
            lambda request: httpx.Response(200, json={"origin": "1.2.3.4"})
        )
        anonymity_transport = httpx.MockTransport(
            lambda request: httpx.Response(200, json={"headers": {}})
        )
        service = ValidateService(
            store=store,
            protocol_validator=ProtocolValidator(),
            connectivity_validator=ConnectivityValidator(
                test_url="https://example.test/ip",
                timeout_seconds=1,
                transport=connectivity_transport,
            ),
            anonymity_validator=AnonymityValidator(
                test_url="https://example.test/headers",
                timeout_seconds=1,
                transport=anonymity_transport,
            ),
            concurrency=2,
            min_elite_score=80,
        )

        outcome = await service.validate_proxy(proxy, from_pool="raw")

        assert outcome.target_pool == "elite"
        assert outcome.proxy.score >= 80
        assert await store.list_proxies("raw") == []
        assert [stored.id for stored in await store.list_proxies("elite")] == [proxy.id]

    asyncio.run(run())


def test_validate_service_moves_failed_proxy_to_cooldown_pool() -> None:
    async def run() -> None:
        store = RedisStore(FakeRedis())
        proxy = await store.add_proxy("raw", make_proxy())

        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("connection failed", request=request)

        service = ValidateService(
            store=store,
            protocol_validator=ProtocolValidator(),
            connectivity_validator=ConnectivityValidator(
                test_url="https://example.test/ip",
                timeout_seconds=1,
                transport=httpx.MockTransport(handler),
            ),
            anonymity_validator=AnonymityValidator(
                test_url="https://example.test/headers",
                timeout_seconds=1,
                transport=httpx.MockTransport(lambda request: httpx.Response(200, json={})),
            ),
            concurrency=2,
            min_elite_score=80,
        )

        outcome = await service.validate_proxy(proxy, from_pool="raw")

        assert outcome.target_pool == "cooldown"
        assert outcome.proxy.fail_count == 1
        assert outcome.proxy.consecutive_fail_count == 1
        assert outcome.proxy.cooldown_until is not None
        assert await store.list_proxies("raw") == []
        assert [stored.id for stored in await store.list_proxies("cooldown")] == [proxy.id]

    asyncio.run(run())


def test_validate_service_moves_repeated_failure_to_dead_pool() -> None:
    async def run() -> None:
        store = RedisStore(FakeRedis())
        proxy = await store.add_proxy(
            "raw",
            make_proxy().model_copy(update={"fail_count": 4, "consecutive_fail_count": 4}),
        )

        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("connection failed", request=request)

        service = ValidateService(
            store=store,
            protocol_validator=ProtocolValidator(),
            connectivity_validator=ConnectivityValidator(
                test_url="https://example.test/ip",
                timeout_seconds=1,
                transport=httpx.MockTransport(handler),
            ),
            anonymity_validator=AnonymityValidator(
                test_url="https://example.test/headers",
                timeout_seconds=1,
                transport=httpx.MockTransport(lambda request: httpx.Response(200, json={})),
            ),
            concurrency=2,
            min_elite_score=80,
        )

        outcome = await service.validate_proxy(proxy, from_pool="raw")

        assert outcome.target_pool == "dead"
        assert outcome.proxy.fail_count == 5
        assert outcome.proxy.consecutive_fail_count == 5
        assert outcome.proxy.cooldown_until is None
        assert await store.list_proxies("raw") == []
        assert [stored.id for stored in await store.list_proxies("dead")] == [proxy.id]

    asyncio.run(run())
