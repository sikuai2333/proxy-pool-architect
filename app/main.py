from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes_dashboard import router as dashboard_router
from app.api.routes_health import router as health_router
from app.api.routes_metrics import router as metrics_router
from app.api.routes_proxy import router as proxy_router
from app.api.routes_stats import router as stats_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.scheduler import SchedulerService
from app.storage.redis_store import RedisStore


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level, structured=settings.log_json)

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        lifespan=_lifespan,
    )
    app.state.store = RedisStore.from_url(settings.redis_url)
    app.state.scheduler = SchedulerService(settings, app.state.store)
    app.state.metrics_enabled = settings.metrics_enabled
    app.include_router(dashboard_router)
    app.include_router(health_router)
    app.include_router(metrics_router)
    app.include_router(proxy_router)
    app.include_router(stats_router)
    return app


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    scheduler = app.state.scheduler
    scheduler.start()
    try:
        yield
    finally:
        scheduler.shutdown()


app = create_app()
