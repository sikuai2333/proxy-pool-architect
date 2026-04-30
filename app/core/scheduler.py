from time import perf_counter

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from loguru import logger

from app.core.config import Settings
from app.providers.manager import ProviderManager
from app.services.fetch_service import FetchService
from app.services.validate_service import ValidateService
from app.storage.redis_store import RedisStore
from app.validators.anonymity import AnonymityValidator
from app.validators.connectivity import ConnectivityValidator
from app.validators.protocol import ProtocolValidator

FETCH_JOB_ID = "fetch_proxies"
VALIDATE_JOB_ID = "validate_proxies"


class SchedulerService:
    def __init__(self, settings: Settings, store: RedisStore) -> None:
        self._settings = settings
        self._store = store
        self._scheduler = AsyncIOScheduler(timezone="UTC")
        self._registered = False

    @property
    def job_ids(self) -> list[str]:
        return [job.id for job in self._scheduler.get_jobs()]

    @property
    def running(self) -> bool:
        return self._scheduler.running

    def register_jobs(self) -> None:
        if self._registered:
            return

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

    async def _run_fetch_job(self) -> None:
        started_at = perf_counter()
        logger.info("Fetch job started")
        try:
            provider_manager = ProviderManager.from_settings(self._settings)
            service = FetchService(provider_manager, self._store)
            proxies = await service.fetch_to_raw_pool()
        except Exception as exc:
            logger.warning("Fetch job failed: {}", exc.__class__.__name__)
            return

        logger.info(
            "Fetch job finished: count={} duration_ms={}",
            len(proxies),
            self._elapsed_ms(started_at),
        )

    async def _run_validate_job(self) -> None:
        started_at = perf_counter()
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
            )
            outcomes = await service.validate_pool(
                pool="raw",
                limit=self._settings.validate_batch_size,
            )
        except Exception as exc:
            logger.warning("Validate job failed: {}", exc.__class__.__name__)
            return

        logger.info(
            "Validate job finished: count={} duration_ms={}",
            len(outcomes),
            self._elapsed_ms(started_at),
        )

    @staticmethod
    def _elapsed_ms(started_at: float) -> int:
        return max(round((perf_counter() - started_at) * 1000), 0)
