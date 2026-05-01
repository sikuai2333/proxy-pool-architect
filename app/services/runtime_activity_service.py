from collections import deque
from datetime import UTC, datetime, timedelta
from itertools import count
from threading import Lock
from typing import TypeVar

from app.models.dashboard import EventLevel, EventLogEntry, ProviderSummary, ValidationJob
from app.models.provider import ProviderFetchResult
from app.utils.time import parse_utc_datetime, utc_now_iso

T = TypeVar("T")


class RuntimeActivityService:
    def __init__(
        self,
        event_limit: int = 200,
        validation_job_limit: int = 50,
        event_retention_seconds: int = 86400,
        validation_job_retention_seconds: int = 604800,
    ) -> None:
        self._events: deque[EventLogEntry] = deque(maxlen=event_limit)
        self._validation_jobs: deque[ValidationJob] = deque(maxlen=validation_job_limit)
        self._provider_states: dict[str, ProviderSummary] = {}
        self._id_counter = count(1)
        self._lock = Lock()
        self._last_fetch_at: str | None = None
        self._last_validate_at: str | None = None
        self._event_retention = timedelta(seconds=event_retention_seconds)
        self._validation_job_retention = timedelta(seconds=validation_job_retention_seconds)

    @property
    def last_fetch_at(self) -> str | None:
        with self._lock:
            return self._last_fetch_at

    @property
    def last_validate_at(self) -> str | None:
        with self._lock:
            return self._last_validate_at

    def record_event(
        self,
        event_type: str,
        level: EventLevel,
        message: str,
        created_at: str | None = None,
    ) -> EventLogEntry:
        event = EventLogEntry(
            id=f"event-{next(self._id_counter):04d}",
            type=event_type,
            level=level,
            message=message,
            created_at=created_at or utc_now_iso(),
        )
        with self._lock:
            self._prune_events_locked()
            self._events.appendleft(event)
        return event

    def list_events(
        self,
        limit: int | None = None,
        offset: int = 0,
    ) -> tuple[list[EventLogEntry], int]:
        with self._lock:
            self._prune_events_locked()
            items = list(self._events)
        total = len(items)
        return _paginate(items, limit=limit, offset=offset), total

    def record_validation_job(self, job: ValidationJob) -> ValidationJob:
        with self._lock:
            self._prune_validation_jobs_locked()
            self._validation_jobs.appendleft(job)
            self._last_validate_at = job.finished_at or job.started_at
        return job

    def list_validation_jobs(
        self,
        limit: int | None = None,
        offset: int = 0,
    ) -> tuple[list[ValidationJob], int]:
        with self._lock:
            self._prune_validation_jobs_locked()
            items = list(self._validation_jobs)
        total = len(items)
        return _paginate(items, limit=limit, offset=offset), total

    def record_provider_fetch_results(
        self,
        results: list[ProviderFetchResult],
        fetched_at: str,
    ) -> None:
        with self._lock:
            self._last_fetch_at = fetched_at
            for result in results:
                current = self._provider_states.get(
                    result.name,
                    ProviderSummary(name=result.name, enabled=result.enabled),
                )
                self._provider_states[result.name] = current.model_copy(
                    update={
                        "enabled": result.enabled,
                        "last_fetch_at": fetched_at,
                        "fetched_count": result.fetched_count,
                        "last_error": result.error,
                    }
                )

    def snapshot_provider_states(self) -> dict[str, ProviderSummary]:
        with self._lock:
            return {name: summary.model_copy() for name, summary in self._provider_states.items()}

    def _prune_events_locked(self) -> None:
        threshold = datetime.now(UTC) - self._event_retention
        while self._events and parse_utc_datetime(self._events[-1].created_at) < threshold:
            self._events.pop()

    def _prune_validation_jobs_locked(self) -> None:
        threshold = datetime.now(UTC) - self._validation_job_retention
        while self._validation_jobs:
            last_item = self._validation_jobs[-1]
            marker = last_item.finished_at or last_item.started_at
            if parse_utc_datetime(marker) >= threshold:
                break
            self._validation_jobs.pop()


def _paginate(items: list[T], *, limit: int | None, offset: int) -> list[T]:
    if limit is None:
        return items[max(offset, 0) :]
    start = max(offset, 0)
    return items[start : start + max(limit, 0)]
