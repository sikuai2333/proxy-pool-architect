from time import perf_counter

import httpx

from app.models.proxy import ProxyEndpoint
from app.models.validation import ValidationResult
from app.utils.proxy_url import format_proxy_url
from app.validators.base import ProxyValidator


class ConnectivityValidator(ProxyValidator):
    def __init__(
        self,
        test_url: str,
        timeout_seconds: float = 10.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._test_url = test_url
        self._timeout = httpx.Timeout(timeout_seconds)
        self._transport = transport

    async def validate(self, proxy: ProxyEndpoint) -> ValidationResult:
        started_at = perf_counter()
        try:
            async with self._build_client(proxy) as client:
                response = await client.get(self._test_url)
        except httpx.TimeoutException:
            return ValidationResult(
                validator="connectivity",
                ok=False,
                error="timeout",
                latency_ms=self._elapsed_ms(started_at),
            )
        except httpx.HTTPError as exc:
            return ValidationResult(
                validator="connectivity",
                ok=False,
                error=exc.__class__.__name__,
                latency_ms=self._elapsed_ms(started_at),
            )
        except Exception as exc:
            return ValidationResult(
                validator="connectivity",
                ok=False,
                error=exc.__class__.__name__,
                latency_ms=self._elapsed_ms(started_at),
            )

        latency_ms = self._elapsed_ms(started_at)
        if response.status_code >= 400:
            return ValidationResult(
                validator="connectivity",
                ok=False,
                latency_ms=latency_ms,
                status_code=response.status_code,
                error=f"status_{response.status_code}",
            )

        return ValidationResult(
            validator="connectivity",
            ok=True,
            latency_ms=latency_ms,
            status_code=response.status_code,
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

    @staticmethod
    def _elapsed_ms(started_at: float) -> int:
        return max(round((perf_counter() - started_at) * 1000), 0)
