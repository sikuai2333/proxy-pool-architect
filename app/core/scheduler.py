import asyncio
from time import perf_counter

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from loguru import logger

from app.core.config import Settings
from app.models.dashboard import ValidationJob
from app.providers.manager import ProviderManager
from app.services.cooldown_service import CooldownService
from app.services.fetch_service import FetchService
from app.services.geo_service import GeoResolver
from app.services.runtime_activity_service import RuntimeActivityService
from app.services.validate_service import ValidateService
from app.storage.sqlite_store import SQLiteStore
from app.utils.time import utc_now_iso
from app.validators.anonymity import AnonymityValidator
from app.validators.connectivity import ConnectivityValidator
from app.validators.protocol import ProtocolValidator

FETCH_JOB_ID = "fetch_proxies"
VALIDATE_JOB_ID = "validate_proxies"


class SchedulerService:
    def __init__(
        self,
        settings: Settings,
        store: SQLiteStore,
        runtime_activity: RuntimeActivityService | None = None,
    ) -> None:
        self._settings = settings
        self._store = store
        self._runtime_activity = runtime_activity or RuntimeActivityService()
        self._scheduler = AsyncIOScheduler(timezone="UTC")
        self._registered = False
        self._validate_lock = asyncio.Lock()

    @property
    def job_ids(self) -> list[str]:
        return [job.id for job in self._scheduler.get_jobs()]

    @property
    def running(self) -> bool:
        return self._scheduler.running

    def register_jobs(self) -> None:
        if self._registered:
            return
        self._upsert_jobs()
        self._registered = True

    def start(self) -> None:
        if not self._settings.scheduler_enabled:
            logger.info("Scheduler disabled")
            return

        self.register_jobs()
        if not self._scheduler.running:
            self._scheduler.start()
            logger.info("Scheduler started with jobs: {}", self.job_ids)

    def shutdown(self) -> None:
        if self._scheduler.running:
            self._scheduler.shutdown(wait=False)
            logger.info("Scheduler stopped")

    def refresh_jobs(self) -> None:
        if not self._settings.scheduler_enabled:
            return
        self._upsert_jobs()
        self._registered = True

    async def run_validate_once(self, limit: int | None = None) -> ValidationJob:
        async with self._validate_lock:
            return await self._execute_validate_job(limit=limit)

    def _upsert_jobs(self) -> None:
        self._scheduler.add_job(
            self._run_fetch_job,
            trigger=IntervalTrigger(seconds=self._settings.fetch_interval_seconds),
            id=FETCH_JOB_ID,
            replace_existing=True,
            max_instances=1,
            coalesce=True,
            misfire_grace_time=30,
        )
        self._scheduler.add_job(
            self._run_validate_job,
            trigger=IntervalTrigger(seconds=self._settings.validate_interval_seconds),
            id=VALIDATE_JOB_ID,
            replace_existing=True,
            max_instances=1,
            coalesce=True,
            misfire_grace_time=30,
        )

    async def _run_fetch_job(self) -> None:
        started_at = perf_counter()
        self._runtime_activity.record_event(
            "fetch_started",
            "info",
            "Background fetch job started.",
        )
        logger.info("Fetch job started")
        try:
            provider_manager = ProviderManager.from_settings(self._settings)
            service = FetchService(
                provider_manager,
                self._store,
                geo_resolver=GeoResolver.from_settings(self._settings),
            )
            report = await service.fetch_to_raw_pool_with_report()
        except Exception as exc:
            self._runtime_activity.record_event(
                "fetch_failed",
                "warning",
                f"Fetch job failed: {exc.__class__.__name__}",
            )
            logger.warning("Fetch job failed: {}", exc.__class__.__name__)
            return

        self._runtime_activity.record_provider_fetch_results(
            report.provider_results,
            report.fetched_at,
        )
        self._runtime_activity.record_event(
            "fetch_finished",
            "info",
            f"Fetch job stored {len(report.stored)} proxies in raw pool.",
            created_at=report.fetched_at,
        )
        logger.info(
            "Fetch job finished: count={} duration_ms={}",
            len(report.stored),
            self._elapsed_ms(started_at),
        )

    async def _run_validate_job(self) -> None:
        await self.run_validate_once()

    async def _execute_validate_job(
        self,
        limit: int | None = None,
    ) -> ValidationJob:
        started_at = perf_counter()
        job_started_at = utc_now_iso()
        self._runtime_activity.record_event(
            "validation_started",
            "info",
            "Background validation job started.",
            created_at=job_started_at,
        )
        logger.info("Validate job started")
        try:
            service = ValidateService(
                store=self._store,
                protocol_validator=ProtocolValidator(),
                connectivity_validator=ConnectivityValidator(
                    test_url=self._settings.test_url,
                    timeout_seconds=self._settings.validate_timeout_seconds,
                ),
                anonymity_validator=AnonymityValidator(
                    test_url=self._settings.anonymity_test_url,
                    timeout_seconds=self._settings.validate_timeout_seconds,
                    original_ip=self._settings.validator_original_ip,
                ),
                concurrency=self._settings.validate_concurrency,
                min_elite_score=self._settings.min_elite_score,
                cooldown_seconds=self._settings.cooldown_seconds,
            )
            released = await CooldownService(self._store).release_expired(
                limit=limit or self._settings.validate_batch_size,
            )
            outcomes = await service.validate_pool(
                pool="raw",
                limit=limit or self._settings.validate_batch_size,
            )
        except Exception as exc:
            finished_at = utc_now_iso()
            failed_job = ValidationJob(
                id=f"job-{round(started_at * 1000)}",
                started_at=job_started_at,
                finished_at=finished_at,
                checked_count=0,
                success_count=0,
                fail_count=0,
                timeout_count=0,
                status="failed",
            )
            self._runtime_activity.record_validation_job(failed_job)
            self._runtime_activity.record_event(
                "validation_failed",
                "warning",
                f"Validation job failed: {exc.__class__.__name__}",
                created_at=finished_at,
            )
            logger.warning("Validate job failed: {}", exc.__class__.__name__)
            return failed_job

        success_count = sum(
            1
            for outcome in outcomes
            if outcome.target_pool in {"checked", "elite"}
        )
        fail_count = len(outcomes) - success_count
        timeout_count = sum(
            1
            for outcome in outcomes
            for result in (outcome.connectivity, outcome.anonymity)
            if (
                result is not None
                and result.error is not None
                and "timeout" in result.error.casefold()
            )
        )
        finished_at = utc_now_iso()
        finished_job = ValidationJob(
            id=f"job-{round(started_at * 1000)}",
            started_at=job_started_at,
            finished_at=finished_at,
            checked_count=len(outcomes),
            success_count=success_count,
            fail_count=fail_count,
            timeout_count=timeout_count,
            status="finished",
        )
        self._runtime_activity.record_validation_job(finished_job)
        self._runtime_activity.record_event(
            "validation_finished",
            "info",
            f"Validation job processed {len(outcomes)} proxies with {success_count} successes.",
            created_at=finished_at,
        )
        logger.info(
            "Validate job finished: released={} validated={} duration_ms={}",
            len(released),
            len(outcomes),
            self._elapsed_ms(started_at),
        )
        return finished_job

    @staticmethod
    def _elapsed_ms(started_at: float) -> int:
        return max(round((perf_counter() - started_at) * 1000), 0)
