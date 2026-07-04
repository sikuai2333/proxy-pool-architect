from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response

from app.api.dependencies import get_store
from app.services.metrics_service import METRICS_CONTENT_TYPE, MetricsService
from app.storage.sqlite_store import SQLiteStore

router = APIRouter(tags=["metrics"])


def get_metrics_service(store: Annotated[SQLiteStore, Depends(get_store)]) -> MetricsService:
    return MetricsService(store)


@router.get("/metrics", response_class=Response)
async def metrics(
    request: Request,
    service: Annotated[MetricsService, Depends(get_metrics_service)],
) -> Response:
    if not request.app.state.metrics_enabled:
        raise HTTPException(status_code=404, detail="metrics disabled")
    return Response(
        content=await service.render_prometheus(),
        media_type=METRICS_CONTENT_TYPE,
    )
