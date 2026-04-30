import pytest

from app.utils.proxy_url import ProxyUrlParseError, parse_proxy_url


@pytest.mark.parametrize(
    ("proxy_url", "expected"),
    [
        (
            "http://1.2.3.4:8080",
            {
                "id": "http-1.2.3.4-8080",
                "scheme": "http",
                "host": "1.2.3.4",
                "port": 8080,
                "username": None,
                "password": None,
            },
        ),
        (
            "https://1.2.3.4:8443",
            {
                "id": "https-1.2.3.4-8443",
                "scheme": "https",
                "host": "1.2.3.4",
                "port": 8443,
                "username": None,
                "password": None,
            },
        ),
        (
            "socks4://1.2.3.4:1080",
            {
                "id": "socks4-1.2.3.4-1080",
                "scheme": "socks4",
                "host": "1.2.3.4",
                "port": 1080,
                "username": None,
                "password": None,
            },
        ),
        (
            "socks5://user:pass@1.2.3.4:1080",
            {
                "id": "socks5-1.2.3.4-1080",
                "scheme": "socks5",
                "host": "1.2.3.4",
                "port": 1080,
                "username": "user",
                "password": "pass",
            },
        ),
    ],
)
def test_parse_proxy_url(proxy_url: str, expected: dict[str, object]) -> None:
    proxy = parse_proxy_url(proxy_url, source="test")

    assert proxy.model_dump(
        include={"id", "scheme", "host", "port", "username", "password"}
    ) == expected
    assert proxy.source == "test"


def test_parse_proxy_url_rejects_unsupported_scheme() -> None:
    with pytest.raises(ProxyUrlParseError):
        parse_proxy_url("ftp://1.2.3.4:21", source="test")
