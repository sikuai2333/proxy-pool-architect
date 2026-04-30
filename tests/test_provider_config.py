import asyncio

from app.core.config import Settings
from app.providers.clash_subscription_provider import ClashSubscriptionProvider
from app.providers.config_loader import build_providers_from_specs, load_provider_specs
from app.providers.core_adapter_provider import CoreAdapterProvider
from app.providers.manager import ProviderManager
from app.providers.static_provider import StaticProvider
from app.providers.tor_provider import TorProvider


def test_load_provider_specs_from_yaml(tmp_path) -> None:
    config_file = tmp_path / "providers.yaml"
    config_file.write_text(
        """
providers:
  - type: static
    enabled: true
    options:
      proxies:
        - "http://1.2.3.4:8080"
  - type: tor
    enabled: false
    options:
      socks_host: "127.0.0.1"
      socks_port: 9050
  - type: core_adapter
    enabled: true
    options:
      core_name: "mihomo"
      local_scheme: "http"
      local_host: "127.0.0.1"
      local_port: 7890
""",
        encoding="utf-8",
    )

    specs = load_provider_specs(str(config_file))
    providers = build_providers_from_specs(specs, Settings())

    assert len(providers) == 3
    assert isinstance(providers[0], StaticProvider)
    assert isinstance(providers[1], TorProvider)
    assert isinstance(providers[2], CoreAdapterProvider)


def test_provider_manager_prefers_yaml_config_when_present(tmp_path) -> None:
    async def run() -> None:
        config_file = tmp_path / "providers.yaml"
        config_file.write_text(
            """
providers:
  - type: static
    enabled: true
    options:
      proxies:
        - "http://1.2.3.4:8080"
""",
            encoding="utf-8",
        )
        settings = Settings(provider_config_file=str(config_file), provider_static_proxies=[])

        proxies = await ProviderManager.from_settings(settings).fetch_all()

        assert [proxy.id for proxy in proxies] == ["http-1.2.3.4-8080"]

    asyncio.run(run())


def test_clash_subscription_provider_parses_supported_nodes() -> None:
    provider = ClashSubscriptionProvider(urls=[], files=[])

    proxies = provider._parse_subscription(
        """
proxies:
  - name: local-http
    type: http
    server: 1.2.3.4
    port: 8080
    username: user
    password: pass
  - name: local-socks
    type: socks5
    server: 1.2.3.5
    port: 1080
  - name: unsupported
    type: vmess
    server: 1.2.3.6
    port: 443
""",
        source_label="test",
    )

    assert [proxy.id for proxy in proxies] == [
        "http-1.2.3.4-8080",
        "socks5-1.2.3.5-1080",
    ]
    assert proxies[0].username == "user"
    assert proxies[0].password == "pass"


def test_tor_provider_returns_local_socks_endpoint() -> None:
    async def run() -> None:
        provider = TorProvider(socks_host="127.0.0.1", socks_port=9050)

        proxies = await provider.fetch()

        assert len(proxies) == 1
        assert proxies[0].id == "socks5-127.0.0.1-9050"
        assert proxies[0].source == "tor"

    asyncio.run(run())


def test_core_adapter_provider_returns_configured_local_inbound() -> None:
    async def run() -> None:
        provider = CoreAdapterProvider(
            core_name="mihomo",
            command=[],
            local_scheme="http",
            local_host="127.0.0.1",
            local_port=7890,
        )

        proxies = await provider.fetch()

        assert len(proxies) == 1
        assert proxies[0].id == "http-127.0.0.1-7890"
        assert proxies[0].source == "core_adapter:mihomo"

    asyncio.run(run())


def test_core_adapter_provider_infers_mixed_port_from_config(tmp_path) -> None:
    async def run() -> None:
        config_file = tmp_path / "mihomo.yaml"
        config_file.write_text("mixed-port: 7890\n", encoding="utf-8")
        provider = CoreAdapterProvider(
            core_name="mihomo",
            command=[],
            config_file=str(config_file),
            local_host="127.0.0.1",
        )

        proxies = await provider.fetch()

        assert len(proxies) == 1
        assert proxies[0].scheme == "http"
        assert proxies[0].port == 7890

    asyncio.run(run())
