from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_runtime_activity, get_scheduler, get_store
from app.core.config import get_settings
from app.core.scheduler import SchedulerService
from app.models.dashboard import (
    DashboardSettings,
    EventListResponse,
    GeoSummaryResponse,
    ProviderListResponse,
    ProviderSummary,
    ValidationJobListResponse,
)
from app.services.dashboard_api_service import DashboardApiService
from app.services.runtime_activity_service import RuntimeActivityService
from app.storage.redis_store import RedisStore

router = APIRouter(tags=["dashboard-api"])


def get_dashboard_api_service(
    store: Annotated[RedisStore, Depends(get_store)],
    scheduler: Annotated[SchedulerService, Depends(get_scheduler)],
    runtime_activity: Annotated[RuntimeActivityService, Depends(get_runtime_activity)],
) -> DashboardApiService:
    return DashboardApiService(
        store=store,
        settings=get_settings(),
        scheduler=scheduler,
        runtime_activity=runtime_activity,
    )


@router.get("/providers", response_model=ProviderListResponse)
async def list_providers(
    service: Annotated[DashboardApiService, Depends(get_dashboard_api_service)],
) -> ProviderListResponse:
    return ProviderListResponse(items=await service.list_provider_summaries())


@router.get("/providers/{provider_name}", response_model=ProviderSummary)
async def get_provider(
    provider_name: str,
    service: Annotated[DashboardApiService, Depends(get_dashboard_api_service)],
) -> ProviderSummary:
    summary = await service.get_provider_summary(provider_name)
    if summary is None:
        raise HTTPException(status_code=404, detail="provider not found")
    return summary


@router.get("/geo/summary", response_model=GeoSummaryResponse)
async def get_geo_summary(
    service: Annotated[DashboardApiService, Depends(get_dashboard_api_service)],
) -> GeoSummaryResponse:
    return await service.get_geo_summary()


@router.get("/validation/jobs", response_model=ValidationJobListResponse)
async def list_validation_jobs(
    service: Annotated[DashboardApiService, Depends(get_dashboard_api_service)],
) -> ValidationJobListResponse:
    return ValidationJobListResponse(items=service.list_validation_jobs())


@router.get("/events", response_model=EventListResponse)
async def list_events(
    service: Annotated[DashboardApiService, Depends(get_dashboard_api_service)],
) -> EventListResponse:
    return EventListResponse(items=service.list_events())


@router.get("/settings", response_model=DashboardSettings)
async def get_dashboard_settings(
    service: Annotated[DashboardApiService, Depends(get_dashboard_api_service)],
) -> DashboardSettings:
    return service.get_settings()


@router.patch("/settings", response_model=DashboardSettings)
async def update_dashboard_settings(
    payload: DashboardSettings,
    service: Annotated[DashboardApiService, Depends(get_dashboard_api_service)],
) -> DashboardSettings:
    return service.update_settings(payload)
