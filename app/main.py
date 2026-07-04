import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.responses import FileResponse, RedirectResponse

from app.api.routes_auth import router as auth_router
from app.api.routes_dashboard_api import router as dashboard_api_router
from app.api.routes_health import router as health_router
from app.api.routes_metrics import router as metrics_router
from app.api.routes_proxy import router as proxy_router
from app.api.routes_stats import router as stats_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.scheduler import SchedulerService
from app.gateway.proxy_gateway import ProxyGateway
from app.services.geo_enrich import enrich_in_background
from app.services.geo_service import GeoResolver
from app.services.runtime_activity_service import RuntimeActivityService
from app.storage.sqlite_store import SQLiteStore

_DIST_DIR = Path(__file__).resolve().parent.parent / "dashboard" / "dist"


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
    app.state.store = SQLiteStore.from_path(settings.db_path)
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

    # --- Proxy gateway ---
    if settings.gateway_enabled:
        app.state.gateway = ProxyGateway(
            store=app.state.store,
            host=settings.gateway_host,
            port=settings.gateway_port,
            default_country=settings.gateway_default_country,
            default_scheme=settings.gateway_default_scheme,
            default_strategy=settings.gateway_default_strategy,
        )
    else:
        app.state.gateway = None

    # --- All API routes under /api ---
    api_prefix = "/api"
    app.include_router(auth_router, prefix=api_prefix)
    app.include_router(dashboard_api_router, prefix=api_prefix)
    app.include_router(health_router, prefix=api_prefix)
    app.include_router(metrics_router, prefix=api_prefix)
    app.include_router(proxy_router, prefix=api_prefix)
    app.include_router(stats_router, prefix=api_prefix)

    # --- Root-level redirects for backward compatibility ---
    @app.get("/health")
    async def health_redirect() -> RedirectResponse:
        return RedirectResponse(url="/api/health", status_code=307)

    @app.get("/metrics")
    async def metrics_redirect() -> RedirectResponse:
        return RedirectResponse(url="/api/metrics", status_code=307)

    # --- Serve React dashboard static files ---
    if _DIST_DIR.is_dir():
        app.mount("/assets", StaticFiles(directory=str(_DIST_DIR / "assets")), name="assets")

        @app.get("/")
        async def serve_index() -> FileResponse:
            return FileResponse(str(_DIST_DIR / "index.html"))

    return app


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    scheduler = app.state.scheduler

    # Retroactively enrich existing proxies with GeoIP data (non-blocking)
    if settings.geo_enabled:
        resolver = GeoResolver.from_settings(settings)
        if resolver is not None:
            asyncio.create_task(enrich_in_background(app.state.store, resolver))

    scheduler.start()
    gateway: ProxyGateway | None = app.state.gateway
    if gateway is not None:
        await gateway.start()
    try:
        yield
    finally:
        if gateway is not None:
            await gateway.stop()
        scheduler.shutdown()
        store: SQLiteStore = app.state.store
        await store.close()


app = create_app()
