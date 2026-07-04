from typing import cast

from fastapi import Request

from app.core.scheduler import SchedulerService
from app.services.runtime_activity_service import RuntimeActivityService
from app.storage.sqlite_store import SQLiteStore


def get_store(request: Request) -> SQLiteStore:
    return cast(SQLiteStore, request.app.state.store)


def get_scheduler(request: Request) -> SchedulerService:
    return cast(SchedulerService, request.app.state.scheduler)


def get_runtime_activity(request: Request) -> RuntimeActivityService:
    return cast(RuntimeActivityService, request.app.state.runtime_activity)
