from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api.routes_auth import router as auth_router
from app.api.routes_dashboard import router as dashboard_router
from app.api.routes_dashboard_api import router as dashboard_api_router
from app.api.routes_health import router as health_router
from app.api.routes_metrics import router as metrics_router
from app.api.routes_proxy import router as proxy_router
from app.api.routes_stats import router as stats_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.scheduler import SchedulerService
from app.services.runtime_activity_service import RuntimeActivityService
from app.storage.redis_store import RedisStore


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level, structured=settings.log_json)

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        lifespan=_lifespan,
    )
    if settings.allowed_hosts:
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts)
    if settings.gzip_minimum_size > 0:
        app.add_middleware(GZipMiddleware, minimum_size=settings.gzip_minimum_size)
    if settings.cors_allowed_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_allowed_origins,
            allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
            allow_headers=["*"],
            allow_credentials=settings.cors_allow_credentials,
        )
    app.state.store = RedisStore.from_url(
        settings.redis_url,
        list_cache_ttl_seconds=settings.proxy_list_cache_ttl_seconds,
    )
    app.state.runtime_activity = RuntimeActivityService(
        event_limit=settings.runtime_event_limit,
        validation_job_limit=settings.runtime_validation_job_limit,
        event_retention_seconds=settings.runtime_event_retention_seconds,
        validation_job_retention_seconds=settings.runtime_validation_job_retention_seconds,
    )
    app.state.scheduler = SchedulerService(
        settings,
        app.state.store,
        runtime_activity=app.state.runtime_activity,
    )
    app.state.metrics_enabled = settings.metrics_enabled
    app.include_router(auth_router)
    app.include_router(dashboard_api_router)
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
