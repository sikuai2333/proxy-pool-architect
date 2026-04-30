from typing import cast
from urllib.parse import unquote, urlparse

from pydantic import ValidationError

from app.models.proxy import ProxyEndpoint, ProxyScheme

SUPPORTED_PROXY_SCHEMES: tuple[ProxyScheme, ...] = ("http", "https", "socks4", "socks5")


class ProxyUrlParseError(ValueError):
    """Raised when a proxy URL cannot be converted to ProxyEndpoint."""


def parse_proxy_url(raw_proxy_url: str, source: str) -> ProxyEndpoint:
    value = raw_proxy_url.strip()
    parsed = urlparse(value)

    if parsed.scheme not in SUPPORTED_PROXY_SCHEMES:
        raise ProxyUrlParseError(f"unsupported proxy scheme: {parsed.scheme or '<missing>'}")
    if parsed.hostname is None:
        raise ProxyUrlParseError("proxy host is required")
    try:
        port = parsed.port
    except ValueError as exc:
        raise ProxyUrlParseError(str(exc)) from exc
    if port is None:
        raise ProxyUrlParseError("proxy port is required")

    scheme = cast(ProxyScheme, parsed.scheme)
    proxy_id = build_proxy_id(scheme, parsed.hostname, port)
    try:
        return ProxyEndpoint(
            id=proxy_id,
            scheme=scheme,
            host=parsed.hostname,
            port=port,
            username=unquote(parsed.username) if parsed.username is not None else None,
            password=unquote(parsed.password) if parsed.password is not None else None,
            source=source,
        )
    except ValueError as exc:
        raise ProxyUrlParseError(str(exc)) from exc
    except ValidationError as exc:
        raise ProxyUrlParseError(str(exc)) from exc


def build_proxy_id(scheme: str, host: str, port: int) -> str:
    normalized_host = host.lower()
    return f"{scheme}-{normalized_host}-{port}"
