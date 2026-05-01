from fastapi import APIRouter, Request

from app.core.config import get_settings
from app.models.health import HealthResponse
from app.services.health_service import build_health_response

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health(request: Request) -> HealthResponse:
    return build_health_response(
        get_settings(),
        scheduler_running=bool(request.app.state.scheduler.running),
    )
