from typing import cast

from fastapi import Request

from app.core.scheduler import SchedulerService
from app.services.runtime_activity_service import RuntimeActivityService
from app.storage.redis_store import RedisStore


def get_store(request: Request) -> RedisStore:
    return cast(RedisStore, request.app.state.store)


def get_scheduler(request: Request) -> SchedulerService:
    return cast(SchedulerService, request.app.state.scheduler)


def get_runtime_activity(request: Request) -> RuntimeActivityService:
    return cast(RuntimeActivityService, request.app.state.runtime_activity)
