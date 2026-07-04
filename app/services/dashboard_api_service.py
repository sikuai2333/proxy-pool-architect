from collections import defaultdict
from pathlib import Path

from app.core.config import Settings
from app.core.scheduler import SchedulerService
from app.models.dashboard import (
    DashboardSettings,
    EventLogEntry,
    GeoAsnSummary,
    GeoCountrySummary,
    GeoCoverageSummary,
    GeoSummaryResponse,
    ProviderSummary,
    SafeNetworkingSettings,
    ValidationJob,
)
from app.models.provider import ProviderFetchResult
from app.models.proxy import ProxyEndpoint
from app.models.url_import import ProxyListFileType, ProxyUrlImportResponse
from app.providers.manager import ProviderManager
from app.services.runtime_activity_service import RuntimeActivityService
from app.services.url_import_service import ProxyUrlImportError, ProxyUrlImportService
from app.storage.sqlite_store import SQLiteStore
from app.utils.time import utc_now_iso


class DashboardApiService:
    def __init__(
        self,
        store: SQLiteStore,
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
        geo_tagged = 0

        for proxy in proxies:
            if proxy.country:
                countries[proxy.country].append(proxy)
            if proxy.asn:
                asns[proxy.asn].append(proxy)
            if proxy.country or proxy.asn:
                geo_tagged += 1

        return GeoSummaryResponse(
            coverage=GeoCoverageSummary(
                total_proxies=len(proxies),
                geo_tagged_proxies=geo_tagged,
                unresolved_proxies=max(len(proxies) - geo_tagged, 0),
                geo_enabled=self._settings.geo_enabled,
                geo_file=self._settings.geo_file,
                geo_file_exists=Path(self._settings.geo_file).exists(),
            ),
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
            fetched_count = fetched_counts.get(name, 0)
            if runtime_summary is not None and runtime_summary.fetched_count > fetched_count:
                fetched_count = runtime_summary.fetched_count
            summaries.append(
                ProviderSummary(
                    name=name,
                    enabled=enabled,
                    last_fetch_at=runtime_summary.last_fetch_at if runtime_summary else None,
                    fetched_count=fetched_count,
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

    async def import_proxies_from_url(
        self,
        *,
        url: str,
        file_type: ProxyListFileType,
    ) -> ProxyUrlImportResponse:
        try:
            result = await ProxyUrlImportService(
                store=self._store,
                settings=self._settings,
            ).import_from_url(url=url, file_type=file_type)
        except ProxyUrlImportError as exc:
            self._runtime_activity.record_event(
                "provider_url_import_failed",
                "warning",
                f"Submitted provider URL import failed: {exc}",
            )
            raise
        self._runtime_activity.record_provider_fetch_results(
            [
                ProviderFetchResult(
                    name=result.source,
                    enabled=True,
                    fetched_count=result.valid_count,
                )
            ],
            fetched_at=utc_now_iso(),
        )
        self._runtime_activity.record_event(
            "provider_url_imported",
            "info",
            (
                f"Imported {result.stored_count} direct proxies from {result.source} "
                f"({result.direct_supported_count} direct, "
                f"{result.adapter_required_count} adapter-required, "
                f"{result.invalid_count} invalid)."
            ),
        )
        return result

    def list_validation_jobs(
        self,
        limit: int,
        offset: int,
    ) -> tuple[list[ValidationJob], int]:
        return self._runtime_activity.list_validation_jobs(limit=limit, offset=offset)

    async def run_validation(self, limit: int | None = None) -> ValidationJob:
        return await self._scheduler.run_validate_once(limit=limit)

    def list_events(
        self,
        limit: int,
        offset: int,
    ) -> tuple[list[EventLogEntry], int]:
        return self._runtime_activity.list_events(limit=limit, offset=offset)

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
