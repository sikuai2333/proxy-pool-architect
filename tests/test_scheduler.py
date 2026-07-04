from app.core.config import Settings
from app.core.scheduler import FETCH_JOB_ID, VALIDATE_JOB_ID, SchedulerService
from app.storage.sqlite_store import SQLiteStore


def test_scheduler_registers_fetch_and_validate_jobs_without_running_them() -> None:
    settings = Settings(
        scheduler_enabled=True,
        fetch_interval_seconds=60,
        validate_interval_seconds=30,
    )
    scheduler = SchedulerService(settings, SQLiteStore(":memory:"))

    scheduler.register_jobs()

    assert set(scheduler.job_ids) == {FETCH_JOB_ID, VALIDATE_JOB_ID}
    assert scheduler.running is False


def test_scheduler_start_is_noop_when_disabled() -> None:
    settings = Settings(scheduler_enabled=False)
    scheduler = SchedulerService(settings, SQLiteStore(":memory:"))

    scheduler.start()

    assert scheduler.running is False
    assert scheduler.job_ids == []
