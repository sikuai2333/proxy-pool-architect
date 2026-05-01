import base64
import json

from app.utils.proxy_text import extract_proxies_from_text, parse_subscription_content


def test_extract_proxies_from_http_text_uses_http_scheme_for_bare_entries() -> None:
    result = extract_proxies_from_text(
        """
        # comment
        1.2.3.4:8080
        user:pass@5.6.7.8:8081
        invalid
        """,
        file_type="http",
        source="manual",
    )

    assert [proxy.id for proxy in result.proxies] == [
        "http-1.2.3.4-8080",
        "http-5.6.7.8-8081",
    ]
    assert result.fetched_count == 2
    assert result.invalid_count == 1
    assert result.valid_count == 2


def test_extract_proxies_from_socks5_text_uses_selected_scheme() -> None:
    result = extract_proxies_from_text(
        "9.9.9.9:1080\n",
        file_type="socks5",
        source="manual",
    )

    assert [proxy.id for proxy in result.proxies] == ["socks5-9.9.9.9-1080"]
    assert result.invalid_count == 0


def test_extract_proxies_from_all_text_supports_mixed_url_formats() -> None:
    result = extract_proxies_from_text(
        """
        http://1.2.3.4:8080
        socks5://user:pass@5.6.7.8:1080
        8.8.8.8:3128
        """,
        file_type="all",
        source="manual",
    )

    assert [proxy.id for proxy in result.proxies] == [
        "http-1.2.3.4-8080",
        "socks5-5.6.7.8-1080",
        "http-8.8.8.8-3128",
    ]
    assert result.fetched_count == 3
    assert result.invalid_count == 0


def test_parse_subscription_content_recognizes_clash_yaml_and_adapter_nodes() -> None:
    result = parse_subscription_content(
        """
proxies:
  - name: local-http
    type: http
    server: 1.2.3.4
    port: 8080
  - name: remote-vmess
    type: vmess
    server: 5.6.7.8
    port: 443
  - name: unknown
    type: custom-x
    server: 9.9.9.9
    port: 9999
""",
        file_type="auto",
        source="manual",
    )

    assert result.detected_format == "clash_yaml"
    assert [proxy.id for proxy in result.proxies] == ["http-1.2.3.4-8080"]
    assert result.direct_supported_count == 1
    assert result.adapter_required_count == 1
    assert result.unsupported_count == 1
    assert result.detected_protocols == ["custom-x", "http", "vmess"]


def test_parse_subscription_content_recognizes_v2ray_base64_subscription() -> None:
    payload = "\n".join(
        [
            "vmess://"
            + base64.b64encode(
                json.dumps({"add": "1.2.3.4", "port": "443", "id": "uuid"}).encode("utf-8")
            ).decode("utf-8"),
            "vless://uuid@5.6.7.8:8443?security=tls#demo",
            "trojan://secret@8.8.8.8:443#demo",
        ]
    )
    subscription = base64.b64encode(payload.encode("utf-8")).decode("utf-8")

    result = parse_subscription_content(
        subscription,
        file_type="auto",
        source="manual",
    )

    assert result.detected_format == "base64_uri_list"
    assert result.direct_supported_count == 0
    assert result.adapter_required_count == 3
    assert result.valid_count == 3
    assert result.detected_protocols == ["trojan", "vless", "vmess"]
