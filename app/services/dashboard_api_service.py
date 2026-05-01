from collections import defaultdict

from app.core.config import Settings
from app.core.scheduler import SchedulerService
from app.models.dashboard import (
    DashboardSettings,
    EventLogEntry,
    GeoAsnSummary,
    GeoCountrySummary,
    GeoSummaryResponse,
    ProviderSummary,
    SafeNetworkingSettings,
    ValidationJob,
)
from app.models.proxy import ProxyEndpoint
from app.providers.manager import ProviderManager
from app.services.runtime_activity_service import RuntimeActivityService
from app.storage.redis_store import RedisStore


class DashboardApiService:
    def __init__(
        self,
        store: RedisStore,
        settings: Settings,
        scheduler: SchedulerService,
        runtime_activity: RuntimeActivityService,
    ) -> None:
        self._store = store
        self._settings = settings
        self._scheduler = scheduler
        self._runtime_activity = runtime_activity

    async def get_geo_summary(self) -> GeoSummaryResponse:
        proxies = await self._store.list_all_proxies()
        countries: defaultdict[str, list[ProxyEndpoint]] = defaultdict(list)
        asns: defaultdict[str, list[ProxyEndpoint]] = defaultdict(list)

        for proxy in proxies:
            if proxy.country:
                countries[proxy.country].append(proxy)
            if proxy.asn:
                asns[proxy.asn].append(proxy)

        return GeoSummaryResponse(
            countries=[
                GeoCountrySummary(
                    country=country,
                    total=len(items),
                    elite=sum(1 for item in items if item.status == "elite"),
                    avg_latency_ms=_average_latency(items),
                )
                for country, items in sorted(
                    countries.items(),
                    key=lambda item: (-len(item[1]), item[0]),
                )
            ],
            asns=[
                GeoAsnSummary(
                    asn=asn,
                    total=len(items),
                    elite=sum(1 for item in items if item.status == "elite"),
                    avg_latency_ms=_average_latency(items),
                )
                for asn, items in sorted(
                    asns.items(),
                    key=lambda item: (-len(item[1]), item[0]),
                )
            ],
        )

    async def list_provider_summaries(self) -> list[ProviderSummary]:
        proxies = await self._store.list_all_proxies()
        configured = {
            provider.name: ProviderSummary(name=provider.name, enabled=provider.enabled)
            for provider in ProviderManager.from_settings(self._settings).providers
        }
        runtime = self._runtime_activity.snapshot_provider_states()

        fetched_counts: dict[str, int] = defaultdict(int)
        valid_counts: dict[str, int] = defaultdict(int)
        for proxy in proxies:
            fetched_counts[proxy.source] += 1
            if proxy.status in {"checked", "elite"}:
                valid_counts[proxy.source] += 1

        names = set(configured) | set(runtime) | set(fetched_counts)
        summaries: list[ProviderSummary] = []
        for name in sorted(names):
            base = configured.get(name) or runtime.get(name)
            enabled = base.enabled if base is not None else fetched_counts.get(name, 0) > 0
            runtime_summary = runtime.get(name)
            summaries.append(
                ProviderSummary(
                    name=name,
                    enabled=enabled,
                    last_fetch_at=runtime_summary.last_fetch_at if runtime_summary else None,
                    fetched_count=fetched_counts.get(name, 0),
                    valid_count=valid_counts.get(name, 0),
                    last_error=runtime_summary.last_error if runtime_summary else None,
                )
            )
        return summaries

    async def get_provider_summary(self, provider_name: str) -> ProviderSummary | None:
        summaries = await self.list_provider_summaries()
        for summary in summaries:
            if summary.name == provider_name:
                return summary
        return None

    def list_validation_jobs(self) -> list[ValidationJob]:
        return self._runtime_activity.list_validation_jobs()

    def list_events(self) -> list[EventLogEntry]:
        return self._runtime_activity.list_events()

    def get_settings(self) -> DashboardSettings:
        return DashboardSettings(
            fetch_interval_seconds=self._settings.fetch_interval_seconds,
            validate_interval_seconds=self._settings.validate_interval_seconds,
            validate_timeout_seconds=self._settings.validate_timeout_seconds,
            validate_concurrency=self._settings.validate_concurrency,
            min_elite_score=self._settings.min_elite_score,
            cooldown_seconds=self._settings.cooldown_seconds,
            safe_networking=SafeNetworkingSettings(
                authorized_targets_only=self._settings.safe_authorized_targets_only,
                block_private_networks=self._settings.safe_block_private_networks,
                mask_proxy_credentials=self._settings.safe_mask_proxy_credentials,
            ),
        )

    def update_settings(self, payload: DashboardSettings) -> DashboardSettings:
        self._settings.fetch_interval_seconds = payload.fetch_interval_seconds
        self._settings.validate_interval_seconds = payload.validate_interval_seconds
        self._settings.validate_timeout_seconds = payload.validate_timeout_seconds
        self._settings.validate_concurrency = payload.validate_concurrency
        self._settings.min_elite_score = payload.min_elite_score
        self._settings.cooldown_seconds = payload.cooldown_seconds
        self._settings.safe_authorized_targets_only = (
            payload.safe_networking.authorized_targets_only
        )
        self._settings.safe_block_private_networks = (
            payload.safe_networking.block_private_networks
        )
        self._settings.safe_mask_proxy_credentials = (
            payload.safe_networking.mask_proxy_credentials
        )
        self._scheduler.refresh_jobs()
        self._runtime_activity.record_event(
            "settings_updated",
            "info",
            "Dashboard runtime settings were updated.",
        )
        return self.get_settings()


def _average_latency(items: list[ProxyEndpoint]) -> float | None:
    latencies = [item.latency_ms for item in items if item.latency_ms is not None]
    if not latencies:
        return None
    return sum(latencies) / len(latencies)
