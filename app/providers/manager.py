from app.core.config import Settings
from app.models.provider import ProviderFetchResult
from app.models.proxy import ProxyEndpoint
from app.providers.base import ProxyProvider
from app.providers.config_loader import build_providers_from_specs, load_provider_specs
from app.providers.static_provider import StaticProvider
from app.providers.url_list_provider import UrlListProvider


class ProviderManager:
    def __init__(self, providers: list[ProxyProvider]) -> None:
        self._providers = providers

    @classmethod
    def from_settings(cls, settings: Settings) -> "ProviderManager":
        provider_specs = load_provider_specs(settings.provider_config_file)
        if provider_specs:
            return cls(build_providers_from_specs(provider_specs, settings))

        return cls(
            providers=[
                StaticProvider(
                    proxies=settings.provider_static_proxies,
                    enabled=settings.provider_static_enabled,
                ),
                UrlListProvider(
                    urls=settings.provider_url_list_urls,
                    enabled=settings.provider_url_lists_enabled,
                    timeout_seconds=settings.provider_url_timeout_seconds,
                    concurrency=settings.provider_url_concurrency,
                ),
            ]
        )

    @property
    def enabled_providers(self) -> list[ProxyProvider]:
        return [provider for provider in self._providers if provider.enabled]

    @property
    def providers(self) -> list[ProxyProvider]:
        return list(self._providers)

    async def fetch_all(self) -> list[ProxyEndpoint]:
        proxies, _ = await self.fetch_all_with_metadata()
        return proxies

    async def fetch_all_with_metadata(
        self,
    ) -> tuple[list[ProxyEndpoint], list[ProviderFetchResult]]:
        proxies: list[ProxyEndpoint] = []
        results: list[ProviderFetchResult] = []
        for provider in self.providers:
            if not provider.enabled:
                results.append(ProviderFetchResult(name=provider.name, enabled=False))
                continue
            try:
                fetched = await provider.fetch()
            except Exception as exc:
                results.append(
                    ProviderFetchResult(
                        name=provider.name,
                        enabled=True,
                        error=exc.__class__.__name__,
                    )
                )
                continue
            proxies.extend(fetched)
            results.append(
                ProviderFetchResult(
                    name=provider.name,
                    enabled=True,
                    fetched_count=len(fetched),
                )
            )
        return proxies, results
