from fastapi import APIRouter

from app.core.config import get_settings
from app.models.health import HealthResponse
from app.services.health_service import build_health_response

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return build_health_response(get_settings())
