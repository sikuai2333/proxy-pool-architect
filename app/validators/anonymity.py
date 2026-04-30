from time import perf_counter
from typing import Any

import httpx

from app.models.proxy import ProxyAnonymity, ProxyEndpoint
from app.models.validation import ValidationResult
from app.utils.proxy_url import format_proxy_url
from app.validators.base import ProxyValidator

LEAK_HEADER_NAMES = {"via", "forwarded", "x-forwarded-for"}


class AnonymityValidator(ProxyValidator):
    def __init__(
        self,
        test_url: str,
        timeout_seconds: float = 10.0,
        original_ip: str | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._test_url = test_url
        self._timeout = httpx.Timeout(timeout_seconds)
        self._original_ip = original_ip
        self._transport = transport

    async def validate(self, proxy: ProxyEndpoint) -> ValidationResult:
        started_at = perf_counter()
        try:
            async with self._build_client(proxy) as client:
                response = await client.get(self._test_url)
        except httpx.TimeoutException:
            return ValidationResult(
                validator="anonymity",
                ok=False,
                error="timeout",
                latency_ms=self._elapsed_ms(started_at),
            )
        except httpx.HTTPError as exc:
            return ValidationResult(
                validator="anonymity",
                ok=False,
                error=exc.__class__.__name__,
                latency_ms=self._elapsed_ms(started_at),
            )
        except Exception as exc:
            return ValidationResult(
                validator="anonymity",
                ok=False,
                error=exc.__class__.__name__,
                latency_ms=self._elapsed_ms(started_at),
            )

        latency_ms = self._elapsed_ms(started_at)
        if response.status_code >= 400:
            return ValidationResult(
                validator="anonymity",
                ok=False,
                latency_ms=latency_ms,
                status_code=response.status_code,
                error=f"status_{response.status_code}",
            )

        anonymity = self._classify_anonymity(response)
        if anonymity == "transparent":
            return ValidationResult(
                validator="anonymity",
                ok=True,
                latency_ms=latency_ms,
                status_code=response.status_code,
                anonymity="transparent",
            )

        return ValidationResult(
            validator="anonymity",
            ok=True,
            latency_ms=latency_ms,
            status_code=response.status_code,
            anonymity=anonymity,
        )

    def _build_client(self, proxy: ProxyEndpoint) -> httpx.AsyncClient:
        if self._transport is not None:
            return httpx.AsyncClient(
                timeout=self._timeout,
                transport=self._transport,
                follow_redirects=False,
            )
        return httpx.AsyncClient(
            timeout=self._timeout,
            proxy=format_proxy_url(proxy),
            follow_redirects=False,
        )

    def _classify_anonymity(self, response: httpx.Response) -> ProxyAnonymity:
        headers = self._extract_observed_headers(response)
        if headers is None:
            if self._original_ip is not None and self._original_ip in response.text:
                return "transparent"
            return "anonymous"

        for header_name, value in headers.items():
            normalized_name = header_name.lower()
            if normalized_name in LEAK_HEADER_NAMES:
                return "transparent"
            if self._original_ip is not None and self._original_ip in str(value):
                return "transparent"
        if self._original_ip is not None and self._original_ip in response.text:
            return "transparent"
        return "elite"

    @staticmethod
    def _extract_observed_headers(response: httpx.Response) -> dict[str, Any] | None:
        try:
            payload = response.json()
        except ValueError:
            return None

        if not isinstance(payload, dict):
            return None

        observed_headers = payload.get("headers", {})
        if isinstance(observed_headers, dict):
            return observed_headers
        return None

    @staticmethod
    def _elapsed_ms(started_at: float) -> int:
        return max(round((perf_counter() - started_at) * 1000), 0)
