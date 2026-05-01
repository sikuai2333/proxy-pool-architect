from collections import deque
from itertools import count
from threading import Lock

from app.models.dashboard import EventLevel, EventLogEntry, ProviderSummary, ValidationJob
from app.models.provider import ProviderFetchResult
from app.utils.time import utc_now_iso


class RuntimeActivityService:
    def __init__(
        self,
        event_limit: int = 200,
        validation_job_limit: int = 50,
    ) -> None:
        self._events: deque[EventLogEntry] = deque(maxlen=event_limit)
        self._validation_jobs: deque[ValidationJob] = deque(maxlen=validation_job_limit)
        self._provider_states: dict[str, ProviderSummary] = {}
        self._id_counter = count(1)
        self._lock = Lock()
        self._last_fetch_at: str | None = None
        self._last_validate_at: str | None = None

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
            self._events.appendleft(event)
        return event

    def list_events(self) -> list[EventLogEntry]:
        with self._lock:
            return list(self._events)

    def record_validation_job(self, job: ValidationJob) -> ValidationJob:
        with self._lock:
            self._validation_jobs.appendleft(job)
            self._last_validate_at = job.finished_at or job.started_at
        return job

    def list_validation_jobs(self) -> list[ValidationJob]:
        with self._lock:
            return list(self._validation_jobs)

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
