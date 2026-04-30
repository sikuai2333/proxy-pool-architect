from importlib import import_module
from pathlib import Path
from typing import Any, cast

import yaml

from app.core.config import Settings
from app.models.provider import ProviderSpec
from app.providers.base import ProxyProvider
from app.providers.clash_subscription_provider import ClashSubscriptionProvider
from app.providers.static_provider import StaticProvider
from app.providers.tor_provider import TorProvider
from app.providers.url_list_provider import UrlListProvider


class ProviderConfigError(ValueError):
    """Raised when provider configuration cannot be loaded safely."""


def load_provider_specs(path: str) -> list[ProviderSpec]:
    config_path = Path(path)
    if not config_path.exists():
        return []

    payload = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    providers = payload.get("providers", [])
    if not isinstance(providers, list):
        raise ProviderConfigError("providers must be a list")
    return [ProviderSpec.model_validate(provider) for provider in providers]


def build_providers_from_specs(
    specs: list[ProviderSpec],
    settings: Settings,
) -> list[ProxyProvider]:
    return [_build_provider(spec, settings) for spec in specs]


def _build_provider(spec: ProviderSpec, settings: Settings) -> ProxyProvider:
    provider_type = spec.type.lower()
    options = spec.options
    if provider_type == "static":
        return StaticProvider(
            proxies=_string_list(options.get("proxies")),
            enabled=spec.enabled,
        )
    if provider_type in {"url_list", "url_lists"}:
        return UrlListProvider(
            urls=_string_list(options.get("urls")),
            enabled=spec.enabled,
            timeout_seconds=float(
                options.get("timeout_seconds", settings.provider_url_timeout_seconds)
            ),
            concurrency=int(options.get("concurrency", settings.provider_url_concurrency)),
        )
    if provider_type in {"clash", "clash_subscription", "flclash"}:
        return ClashSubscriptionProvider(
            urls=_string_list(options.get("urls")),
            files=_string_list(options.get("files")),
            enabled=spec.enabled,
            timeout_seconds=float(
                options.get("timeout_seconds", settings.provider_url_timeout_seconds)
            ),
            concurrency=int(options.get("concurrency", settings.provider_url_concurrency)),
        )
    if provider_type == "tor":
        return TorProvider(
            socks_host=str(options.get("socks_host", "127.0.0.1")),
            socks_port=int(options.get("socks_port", 9050)),
            enabled=spec.enabled,
        )
    if provider_type == "custom":
        if spec.class_path is None:
            raise ProviderConfigError("custom provider requires class_path")
        provider_class = _load_provider_class(
            spec.class_path,
            settings.provider_plugin_allowed_prefixes,
        )
        provider_factory = cast(Any, provider_class)
        return cast(ProxyProvider, provider_factory(enabled=spec.enabled, **options))

    raise ProviderConfigError(f"unsupported provider type: {spec.type}")


def _load_provider_class(
    class_path: str,
    allowed_prefixes: list[str],
) -> type[ProxyProvider]:
    if not any(class_path.startswith(prefix) for prefix in allowed_prefixes):
        raise ProviderConfigError(f"provider class is not allowed: {class_path}")

    module_name, _, class_name = class_path.rpartition(".")
    if not module_name or not class_name:
        raise ProviderConfigError(f"invalid provider class path: {class_path}")

    module = import_module(module_name)
    provider_class = getattr(module, class_name)
    if not issubclass(provider_class, ProxyProvider):
        raise ProviderConfigError(f"class is not a ProxyProvider: {class_path}")
    return cast(type[ProxyProvider], provider_class)


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    raise ProviderConfigError("expected a list of strings")
