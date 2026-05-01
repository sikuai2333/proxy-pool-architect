from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger

from app.api.auth import require_admin_auth
from app.api.dependencies import get_runtime_activity, get_scheduler, get_store
from app.core.config import get_settings
from app.core.scheduler import SchedulerService
from app.models.dashboard import (
    DashboardSettings,
    EventListResponse,
    GeoSummaryResponse,
    ProviderListResponse,
    ProviderSummary,
    ValidationJob,
    ValidationJobListResponse,
)
from app.models.url_import import ProxyUrlImportRequest, ProxyUrlImportResponse
from app.services.dashboard_api_service import DashboardApiService
from app.services.runtime_activity_service import RuntimeActivityService
from app.services.url_import_service import ProxyUrlImportError
from app.storage.redis_store import RedisStore

router = APIRouter(tags=["dashboard-api"], dependencies=[Depends(require_admin_auth)])


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


@router.post("/providers/import-url", response_model=ProxyUrlImportResponse)
async def import_provider_url(
    payload: ProxyUrlImportRequest,
    service: Annotated[DashboardApiService, Depends(get_dashboard_api_service)],
) -> ProxyUrlImportResponse:
    try:
        result = await service.import_proxies_from_url(
            url=str(payload.url),
            file_type=payload.file_type,
        )
    except ProxyUrlImportError as exc:
        logger.warning(
            "Provider URL import failed file_type={} detail={}",
            payload.file_type,
            str(exc),
        )
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc

    logger.info(
        (
            "Provider URL import completed source={} format={} stored={} "
            "direct={} adapter={} invalid={}"
        ),
        result.source,
        result.detected_format,
        result.stored_count,
        result.direct_supported_count,
        result.adapter_required_count,
        result.invalid_count,
    )
    return result


@router.get("/geo/summary", response_model=GeoSummaryResponse)
async def get_geo_summary(
    service: Annotated[DashboardApiService, Depends(get_dashboard_api_service)],
) -> GeoSummaryResponse:
    return await service.get_geo_summary()


@router.get("/validation/jobs", response_model=ValidationJobListResponse)
async def list_validation_jobs(
    service: Annotated[DashboardApiService, Depends(get_dashboard_api_service)],
    limit: Annotated[int, Query(ge=1, le=500)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ValidationJobListResponse:
    items, total = service.list_validation_jobs(limit=limit, offset=offset)
    return ValidationJobListResponse(items=items, total=total, limit=limit, offset=offset)


@router.post("/validation/run", response_model=ValidationJob)
async def run_validation(
    service: Annotated[DashboardApiService, Depends(get_dashboard_api_service)],
    limit: Annotated[int | None, Query(ge=1, le=5000)] = None,
) -> ValidationJob:
    return await service.run_validation(limit=limit)


@router.get("/events", response_model=EventListResponse)
async def list_events(
    service: Annotated[DashboardApiService, Depends(get_dashboard_api_service)],
    limit: Annotated[int, Query(ge=1, le=500)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> EventListResponse:
    items, total = service.list_events(limit=limit, offset=offset)
    return EventListResponse(items=items, total=total, limit=limit, offset=offset)


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
