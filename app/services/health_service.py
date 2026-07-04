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
        db_configured=bool(settings.db_path),
        db="ok" if settings.db_path else "unknown",
        scheduler="running" if scheduler_running else "stopped",
    )
