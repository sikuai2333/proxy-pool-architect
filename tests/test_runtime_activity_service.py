from datetime import UTC, datetime, timedelta

from app.models.dashboard import ValidationJob
from app.services.runtime_activity_service import RuntimeActivityService


def iso_ago(*, seconds: int) -> str:
    return (datetime.now(UTC) - timedelta(seconds=seconds)).isoformat()


def test_runtime_activity_service_paginates_events_and_jobs() -> None:
    service = RuntimeActivityService()
    service.record_event("event-1", "info", "first", created_at=iso_ago(seconds=10))
    service.record_event("event-2", "warning", "second", created_at=iso_ago(seconds=5))
    service.record_validation_job(
        ValidationJob(
            id="job-001",
            started_at=iso_ago(seconds=20),
            finished_at=iso_ago(seconds=19),
            checked_count=5,
            success_count=2,
            fail_count=3,
            timeout_count=1,
            status="finished",
        )
    )
    service.record_validation_job(
        ValidationJob(
            id="job-002",
            started_at=iso_ago(seconds=15),
            finished_at=iso_ago(seconds=14),
            checked_count=8,
            success_count=4,
            fail_count=4,
            timeout_count=0,
            status="finished",
        )
    )

    events, event_total = service.list_events(limit=1, offset=1)
    jobs, job_total = service.list_validation_jobs(limit=1, offset=1)

    assert event_total == 2
    assert events[0].type == "event-1"
    assert job_total == 2
    assert jobs[0].id == "job-001"


def test_runtime_activity_service_prunes_expired_events_and_jobs() -> None:
    service = RuntimeActivityService(
        event_retention_seconds=60,
        validation_job_retention_seconds=60,
    )
    service.record_event("expired", "info", "old", created_at=iso_ago(seconds=120))
    service.record_event("fresh", "info", "new", created_at=iso_ago(seconds=10))
    service.record_validation_job(
        ValidationJob(
            id="job-expired",
            started_at=iso_ago(seconds=120),
            finished_at=iso_ago(seconds=119),
            checked_count=1,
            success_count=0,
            fail_count=1,
            timeout_count=0,
            status="finished",
        )
    )
    service.record_validation_job(
        ValidationJob(
            id="job-fresh",
            started_at=iso_ago(seconds=20),
            finished_at=iso_ago(seconds=19),
            checked_count=1,
            success_count=1,
            fail_count=0,
            timeout_count=0,
            status="finished",
        )
    )

    events, event_total = service.list_events(limit=10, offset=0)
    jobs, job_total = service.list_validation_jobs(limit=10, offset=0)

    assert event_total == 1
    assert events[0].type == "fresh"
    assert job_total == 1
    assert jobs[0].id == "job-fresh"
