from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import get_store
from app.models.api import StatsResponse
from app.services.stats_service import StatsService
from app.storage.redis_store import RedisStore

router = APIRouter(tags=["stats"])


def get_stats_service(store: Annotated[RedisStore, Depends(get_store)]) -> StatsService:
    return StatsService(store)


@router.get("/stats", response_model=StatsResponse)
async def get_stats(
    service: Annotated[StatsService, Depends(get_stats_service)],
) -> StatsResponse:
    return await service.get_stats()
