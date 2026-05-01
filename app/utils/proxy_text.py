from __future__ import annotations

import base64
import binascii
import json
import re
from dataclasses import dataclass
from typing import Literal
from urllib.parse import urlparse

import yaml

from app.models.proxy import ProxyEndpoint
from app.models.url_import import ProxyListFileType, SubscriptionDetectedFormat
from app.utils.proxy_url import ProxyUrlParseError, parse_proxy_url

_FULL_PROXY_RE = re.compile(
    r"(?P<proxy>"
    r"(?P<scheme>https?|socks4|socks5)://"
    r"(?:(?P<username>[^:@/\s]+)(?::(?P<password>[^@/\s]*))?@)?"
    r"(?P<host>\[[0-9A-Fa-f:.]+\]|(?:\d{1,3}\.){3}\d{1,3}|[A-Za-z0-9.-]+)"
    r":(?P<port>\d{1,5})"
    r")",
    re.IGNORECASE,
)
_BARE_PROXY_RE = re.compile(
    r"(?P<proxy>"
    r"(?:(?P<username>[^:@/\s]+)(?::(?P<password>[^@/\s]*))?@)?"
    r"(?P<host>\[[0-9A-Fa-f:.]+\]|(?:\d{1,3}\.){3}\d{1,3}|[A-Za-z0-9.-]+)"
    r":(?P<port>\d{1,5})"
    r")",
    re.IGNORECASE,
)
_BASE64_CHARS_RE = re.compile(r"^[A-Za-z0-9+/=\s_-]+$")
_DIRECT_SCHEMES = {"http", "https", "socks4", "socks5"}
_ADAPTER_SCHEMES = {
    "vmess",
    "vless",
    "trojan",
    "ss",
    "ssr",
    "hysteria",
    "hysteria2",
    "hy2",
    "tuic",
    "wireguard",
    "snell",
}
_CLASH_DIRECT_TYPES = {"http", "socks4", "socks5"}
_CLASH_ADAPTER_TYPES = {
    "vmess",
    "vless",
    "trojan",
    "ss",
    "ssr",
    "hysteria",
    "hysteria2",
    "hy2",
    "tuic",
    "wireguard",
    "snell",
}


@dataclass(frozen=True)
class ProxyTextParseResult:
    proxies: list[ProxyEndpoint]
    fetched_count: int
    invalid_count: int

    @property
    def valid_count(self) -> int:
        return len(self.proxies)


SubscriptionConnectionMode = Literal["direct", "core_adapter", "unsupported"]


@dataclass(frozen=True)
class ParsedSubscriptionEntry:
    protocol: str
    connection_mode: SubscriptionConnectionMode
    proxy: ProxyEndpoint | None = None


@dataclass(frozen=True)
class SubscriptionParseResult:
    detected_format: SubscriptionDetectedFormat
    entries: list[ParsedSubscriptionEntry]
    fetched_count: int
    invalid_count: int

    @property
    def direct_supported_count(self) -> int:
        return sum(1 for entry in self.entries if entry.connection_mode == "direct")

    @property
    def adapter_required_count(self) -> int:
        return sum(1 for entry in self.entries if entry.connection_mode == "core_adapter")

    @property
    def unsupported_count(self) -> int:
        return sum(1 for entry in self.entries if entry.connection_mode == "unsupported")

    @property
    def valid_count(self) -> int:
        return self.direct_supported_count + self.adapter_required_count

    @property
    def proxies(self) -> list[ProxyEndpoint]:
        return [entry.proxy for entry in self.entries if entry.proxy is not None]

    @property
    def detected_protocols(self) -> list[str]:
        return sorted({entry.protocol for entry in self.entries})

    @property
    def supported_connection_modes(self) -> list[Literal["direct", "core_adapter"]]:
        modes: list[Literal["direct", "core_adapter"]] = []
        if self.direct_supported_count:
            modes.append("direct")
        if self.adapter_required_count:
            modes.append("core_adapter")
        return modes


def extract_proxies_from_text(
    content: str,
    *,
    file_type: ProxyListFileType,
    source: str,
) -> ProxyTextParseResult:
    proxies: list[ProxyEndpoint] = []
    fetched_count = 0
    invalid_count = 0
    default_scheme = _default_scheme(file_type)

    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line or line.startswith(("#", ";", "//")):
            continue

        candidate = _extract_candidate(line, default_scheme=default_scheme)
        if candidate is None:
            invalid_count += 1
            continue

        fetched_count += 1
        try:
            proxies.append(parse_proxy_url(candidate, source=source))
        except ProxyUrlParseError:
            invalid_count += 1

    return ProxyTextParseResult(
        proxies=proxies,
        fetched_count=fetched_count,
        invalid_count=invalid_count,
    )


def parse_subscription_content(
    content: str,
    *,
    file_type: ProxyListFileType,
    source: str,
) -> SubscriptionParseResult:
    if file_type == "clash":
        return _parse_clash_or_text(content, source=source, fallback_default_scheme="http")

    if file_type == "v2ray":
        decoded = _maybe_decode_base64_text(content)
        text = decoded or content
        return _parse_uri_subscription_text(
            text,
            source=source,
            detected_format="base64_uri_list" if decoded else "v2ray_uri_list",
            default_scheme=None,
        )

    if file_type == "auto":
        clash_result = _try_parse_clash(content, source=source)
        if clash_result is not None:
            return clash_result

        decoded = _maybe_decode_base64_text(content)
        if decoded is not None and _looks_like_uri_subscription(decoded):
            return _parse_uri_subscription_text(
                decoded,
                source=source,
                detected_format="base64_uri_list",
                default_scheme=None,
            )

        return _parse_uri_subscription_text(
            content,
            source=source,
            detected_format="plain_text",
            default_scheme="http",
        )

    if file_type in {"http", "socks5", "all"}:
        default_scheme = _default_scheme(file_type)
        return _parse_uri_subscription_text(
            content,
            source=source,
            detected_format="plain_text",
            default_scheme=default_scheme,
        )

    return _parse_uri_subscription_text(
        content,
        source=source,
        detected_format="plain_text",
        default_scheme="http",
    )


def _extract_candidate(line: str, *, default_scheme: str | None) -> str | None:
    full_match = _FULL_PROXY_RE.search(line)
    if full_match is not None:
        return full_match.group("proxy")

    bare_match = _BARE_PROXY_RE.search(line)
    if bare_match is None or default_scheme is None:
        return None
    return f"{default_scheme}://{bare_match.group('proxy')}"


def _default_scheme(file_type: ProxyListFileType) -> str | None:
    if file_type == "http":
        return "http"
    if file_type == "socks5":
        return "socks5"
    return "http"


def _parse_clash_or_text(
    content: str,
    *,
    source: str,
    fallback_default_scheme: str | None,
) -> SubscriptionParseResult:
    clash_result = _try_parse_clash(content, source=source)
    if clash_result is not None:
        return clash_result
    return _parse_uri_subscription_text(
        content,
        source=source,
        detected_format="plain_text",
        default_scheme=fallback_default_scheme,
    )


def _try_parse_clash(content: str, *, source: str) -> SubscriptionParseResult | None:
    try:
        payload = yaml.safe_load(content)
    except yaml.YAMLError:
        return None
    if not isinstance(payload, dict) or not isinstance(payload.get("proxies"), list):
        return None

    entries: list[ParsedSubscriptionEntry] = []
    fetched_count = 0
    invalid_count = 0
    for node in payload["proxies"]:
        if not isinstance(node, dict):
            continue
        fetched_count += 1
        entry = _parse_clash_node(node, source=source)
        if entry is None:
            invalid_count += 1
            continue
        entries.append(entry)

    return SubscriptionParseResult(
        detected_format="clash_yaml",
        entries=entries,
        fetched_count=fetched_count,
        invalid_count=invalid_count,
    )


def _parse_clash_node(node: dict[object, object], *, source: str) -> ParsedSubscriptionEntry | None:
    node_type = str(node.get("type", "")).lower()
    if node_type in _CLASH_DIRECT_TYPES:
        server = node.get("server")
        port = node.get("port")
        if server is None or port is None:
            return None

        username = node.get("username") or node.get("user")
        password = node.get("password") or node.get("pass")
        credential_prefix = ""
        if username is not None:
            credential_prefix = str(username)
            if password is not None:
                credential_prefix = f"{credential_prefix}:{password}"
            credential_prefix = f"{credential_prefix}@"

        try:
            parsed_port = int(str(port))
            proxy = parse_proxy_url(
                f"{node_type}://{credential_prefix}{server}:{parsed_port}",
                source=source,
            )
        except (ValueError, ProxyUrlParseError):
            return None
        return ParsedSubscriptionEntry(protocol=node_type, connection_mode="direct", proxy=proxy)

    if node_type in _CLASH_ADAPTER_TYPES:
        return ParsedSubscriptionEntry(
            protocol=_normalize_protocol(node_type),
            connection_mode="core_adapter",
        )

    if node_type:
        return ParsedSubscriptionEntry(protocol=node_type, connection_mode="unsupported")
    return None


def _parse_uri_subscription_text(
    content: str,
    *,
    source: str,
    detected_format: SubscriptionDetectedFormat,
    default_scheme: str | None,
) -> SubscriptionParseResult:
    entries: list[ParsedSubscriptionEntry] = []
    fetched_count = 0
    invalid_count = 0

    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line or line.startswith(("#", ";", "//")):
            continue

        fetched_count += 1
        entry = _parse_subscription_line(line, source=source, default_scheme=default_scheme)
        if entry is None:
            invalid_count += 1
            continue
        entries.append(entry)

    return SubscriptionParseResult(
        detected_format=detected_format,
        entries=entries,
        fetched_count=fetched_count,
        invalid_count=invalid_count,
    )


def _parse_subscription_line(
    line: str,
    *,
    source: str,
    default_scheme: str | None,
) -> ParsedSubscriptionEntry | None:
    candidate = _extract_candidate(line, default_scheme=default_scheme)
    if candidate is not None:
        try:
            proxy = parse_proxy_url(candidate, source=source)
        except ProxyUrlParseError:
            return None
        return ParsedSubscriptionEntry(
            protocol=proxy.scheme,
            connection_mode="direct",
            proxy=proxy,
        )

    parsed = urlparse(line)
    scheme = parsed.scheme.casefold()
    if scheme in _DIRECT_SCHEMES:
        try:
            proxy = parse_proxy_url(line, source=source)
        except ProxyUrlParseError:
            return None
        return ParsedSubscriptionEntry(protocol=proxy.scheme, connection_mode="direct", proxy=proxy)

    if scheme in _ADAPTER_SCHEMES:
        return _parse_adapter_entry(line, scheme)

    return None


def _parse_adapter_entry(line: str, scheme: str) -> ParsedSubscriptionEntry | None:
    protocol = _normalize_protocol(scheme)
    if scheme == "vmess":
        decoded_payload = _decode_vmess_payload(line)
        if decoded_payload is None:
            return None
        return ParsedSubscriptionEntry(protocol=protocol, connection_mode="core_adapter")

    if scheme == "ssr":
        decoded_text = _decode_ssr_payload(line)
        if decoded_text is None:
            return None
        return ParsedSubscriptionEntry(protocol=protocol, connection_mode="core_adapter")

    parsed = urlparse(line)
    if parsed.hostname is None and "@" not in parsed.netloc:
        return None
    return ParsedSubscriptionEntry(protocol=protocol, connection_mode="core_adapter")


def _looks_like_uri_subscription(content: str) -> bool:
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line or line.startswith(("#", ";", "//")):
            continue
        parsed = urlparse(line)
        if parsed.scheme.casefold() in _DIRECT_SCHEMES | _ADAPTER_SCHEMES:
            return True
    return False


def _maybe_decode_base64_text(content: str) -> str | None:
    stripped = "".join(content.split())
    if not stripped or len(stripped) < 16 or not _BASE64_CHARS_RE.fullmatch(stripped):
        return None

    candidates = [stripped]
    if "-" in stripped or "_" in stripped:
        candidates.append(stripped.replace("-", "+").replace("_", "/"))

    for candidate in candidates:
        padded = _pad_base64(candidate)
        try:
            decoded = base64.b64decode(padded, validate=True)
        except (ValueError, binascii.Error):
            continue
        try:
            text = decoded.decode("utf-8")
        except UnicodeDecodeError:
            continue
        if _looks_like_uri_subscription(text) or "proxies:" in text:
            return text
    return None


def _decode_vmess_payload(line: str) -> dict[str, object] | None:
    payload = line.partition("://")[2].strip()
    try:
        decoded = base64.b64decode(_pad_base64(payload)).decode("utf-8")
    except (ValueError, UnicodeDecodeError, binascii.Error):
        return None
    try:
        parsed = json.loads(decoded)
    except json.JSONDecodeError:
        return None
    if not isinstance(parsed, dict):
        return None
    return parsed


def _decode_ssr_payload(line: str) -> str | None:
    payload = line.partition("://")[2].strip()
    try:
        decoded = base64.urlsafe_b64decode(_pad_base64(payload)).decode("utf-8")
    except (ValueError, UnicodeDecodeError, binascii.Error):
        return None
    return decoded or None


def _pad_base64(value: str) -> str:
    remainder = len(value) % 4
    if remainder == 0:
        return value
    return value + ("=" * (4 - remainder))


def _normalize_protocol(protocol: str) -> str:
    if protocol == "hy2":
        return "hysteria2"
    return protocol
