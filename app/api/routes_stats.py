from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.auth import require_admin_auth
from app.api.dependencies import get_runtime_activity, get_scheduler, get_store
from app.core.scheduler import SchedulerService
from app.models.api import StatsResponse
from app.services.runtime_activity_service import RuntimeActivityService
from app.services.stats_service import StatsService
from app.storage.sqlite_store import SQLiteStore

router = APIRouter(tags=["stats"], dependencies=[Depends(require_admin_auth)])


def get_stats_service(store: Annotated[SQLiteStore, Depends(get_store)]) -> StatsService:
    return StatsService(store)


@router.get("/stats", response_model=StatsResponse)
async def get_stats(
    service: Annotated[StatsService, Depends(get_stats_service)],
    scheduler: Annotated[SchedulerService, Depends(get_scheduler)],
    runtime_activity: Annotated[RuntimeActivityService, Depends(get_runtime_activity)],
) -> StatsResponse:
    stats = await service.get_stats()
    return stats.model_copy(
        update={
            "raw": stats.pools.get("raw", 0),
            "checked": stats.pools.get("checked", 0),
            "elite": stats.pools.get("elite", 0),
            "dead": stats.pools.get("dead", 0),
            "cooldown": stats.pools.get("cooldown", 0),
            "last_fetch_at": runtime_activity.last_fetch_at,
            "last_validate_at": runtime_activity.last_validate_at,
            "db_status": "ok",
            "scheduler_status": "running" if scheduler.running else "stopped",
        }
    )
