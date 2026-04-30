from fastapi import FastAPI

from app.api.routes_health import router as health_router
from app.api.routes_proxy import router as proxy_router
from app.api.routes_stats import router as stats_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.storage.redis_store import RedisStore


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(title=settings.app_name, version=settings.app_version)
    app.state.store = RedisStore.from_url(settings.redis_url)
    app.include_router(health_router)
    app.include_router(proxy_router)
    app.include_router(stats_router)
    return app


app = create_app()
