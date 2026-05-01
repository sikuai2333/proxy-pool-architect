from app.core.config import Settings
from app.models.health import HealthResponse


def build_health_response(
    settings: Settings,
    scheduler_running: bool = False,
) -> HealthResponse:
    return HealthResponse(
        status="ok",
        app=settings.app_name,
        version=settings.app_version,
        environment=settings.app_env,
        redis_configured=bool(settings.redis_url),
        redis="ok" if settings.redis_url else "unknown",
        scheduler="running" if scheduler_running else "stopped",
    )
