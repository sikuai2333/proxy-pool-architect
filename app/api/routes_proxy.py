from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import PlainTextResponse
from loguru import logger

from app.api.auth import require_admin_auth
from app.api.dependencies import get_runtime_activity, get_store
from app.core.config import get_settings
from app.models.api import (
    DeleteProxyResponse,
    ProxyListResponse,
    ProxyResponse,
    ProxyResponseFormat,
    ReportProxyRequest,
    ReportProxyResponse,
)
from app.models.proxy import ProxyAnonymity, ProxyFilters, ProxyPool, ProxyScheme
from app.services.proxy_service import ProxyService
from app.services.runtime_activity_service import RuntimeActivityService
from app.storage.redis_store import RedisStore
from app.utils.proxy_url import format_proxy_url

router = APIRouter(tags=["proxy"], dependencies=[Depends(require_admin_auth)])


def get_proxy_service(store: Annotated[RedisStore, Depends(get_store)]) -> ProxyService:
    settings = get_settings()
    return ProxyService(
        store,
        cooldown_seconds=settings.cooldown_seconds,
        session_affinity_ttl_seconds=settings.session_affinity_ttl_seconds,
    )


@router.get(
    "/proxy",
    response_model=ProxyResponse,
    responses={200: {"content": {"application/json": {}, "text/plain": {}}}},
)
async def get_proxy(
    service: Annotated[ProxyService, Depends(get_proxy_service)],
    scheme: ProxyScheme | None = None,
    anonymity: ProxyAnonymity | None = None,
    country: str | None = None,
    min_score: int | None = None,
    session_id: Annotated[str | None, Query(min_length=1, max_length=128)] = None,
    response_format: Annotated[ProxyResponseFormat, Query(alias="format")] = "json",
) -> ProxyResponse | PlainTextResponse:
    proxy = await service.get_proxy(
        ProxyFilters(
            scheme=scheme,
            anonymity=anonymity,
            country=country,
            min_score=min_score,
        ),
        session_id=session_id,
    )
    if proxy is None:
        raise HTTPException(status_code=404, detail="proxy not found")
    if response_format == "text":
        return PlainTextResponse(format_proxy_url(proxy, include_credentials=False))
    return ProxyResponse.from_endpoint(proxy)


@router.get("/proxy/list", response_model=ProxyListResponse)
async def list_proxies(
    service: Annotated[ProxyService, Depends(get_proxy_service)],
    pool: ProxyPool | None = None,
    scheme: ProxyScheme | None = None,
    anonymity: ProxyAnonymity | None = None,
    country: str | None = None,
    source: str | None = None,
    q: Annotated[str | None, Query(min_length=1, max_length=255)] = None,
    min_score: int | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ProxyListResponse:
    proxies, total = await service.list_proxies(
        pool=pool,
        filters=ProxyFilters(
            scheme=scheme,
            anonymity=anonymity,
            country=country,
            source=source,
            query=q,
            min_score=min_score,
        ),
        limit=limit,
        offset=offset,
    )
    logger.debug(
        "Listed proxies pool={} total={} returned={} limit={} offset={} filtered={}",
        pool or "all",
        total,
        len(proxies),
        limit,
        offset,
        bool(scheme or anonymity or country or source or q or min_score is not None),
    )
    responses = [ProxyResponse.from_endpoint(proxy) for proxy in proxies]
    return ProxyListResponse(
        items=responses,
        total=total,
        proxies=responses,
        count=len(responses),
        limit=limit,
        offset=offset,
    )


@router.get("/proxy/{proxy_id}", response_model=ProxyResponse)
async def get_proxy_detail(
    proxy_id: str,
    service: Annotated[ProxyService, Depends(get_proxy_service)],
) -> ProxyResponse:
    proxy = await service.get_proxy_detail(proxy_id)
    if proxy is None:
        raise HTTPException(status_code=404, detail="proxy not found")
    return ProxyResponse.from_endpoint(proxy)


@router.post("/proxy/report", response_model=ReportProxyResponse)
async def report_proxy_result(
    report: ReportProxyRequest,
    service: Annotated[ProxyService, Depends(get_proxy_service)],
    runtime_activity: Annotated[RuntimeActivityService, Depends(get_runtime_activity)],
) -> ReportProxyResponse:
    proxy = await service.report_result(report)
    if proxy is None:
        logger.info("Proxy report missed proxy_id={} ok={}", report.proxy_id, report.ok)
        raise HTTPException(status_code=404, detail="proxy not found")
    if not report.ok:
        runtime_activity.record_event(
            "proxy_reported_failure",
            "warning",
            f"Proxy {proxy.id} was reported as failed.",
        )
        logger.info(
            "Proxy report recorded proxy_id={} ok={} status={} score={}",
            proxy.id,
            report.ok,
            proxy.status,
            proxy.score,
        )
    else:
        logger.debug(
            "Proxy report recorded proxy_id={} ok={} status={} score={}",
            proxy.id,
            report.ok,
            proxy.status,
            proxy.score,
        )
    return ReportProxyResponse(
        proxy_id=proxy.id,
        status=proxy.status,
        score=proxy.score,
        success_count=proxy.success_count,
        fail_count=proxy.fail_count,
    )


@router.delete("/proxy/{proxy_id}", response_model=DeleteProxyResponse)
async def delete_proxy(
    proxy_id: str,
    service: Annotated[ProxyService, Depends(get_proxy_service)],
    runtime_activity: Annotated[RuntimeActivityService, Depends(get_runtime_activity)],
) -> DeleteProxyResponse:
    deleted = await service.delete_proxy(proxy_id)
    if not deleted:
        logger.info("Proxy delete missed proxy_id={}", proxy_id)
        raise HTTPException(status_code=404, detail="proxy not found")
    runtime_activity.record_event(
        "proxy_deleted",
        "info",
        f"Proxy {proxy_id} was deleted from the pool.",
    )
    logger.info("Proxy deleted proxy_id={}", proxy_id)
    return DeleteProxyResponse(proxy_id=proxy_id, deleted=True, ok=True)
