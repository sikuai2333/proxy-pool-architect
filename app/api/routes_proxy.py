from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import PlainTextResponse

from app.api.dependencies import get_store
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
from app.storage.redis_store import RedisStore
from app.utils.proxy_url import format_proxy_url

router = APIRouter(tags=["proxy"])


def get_proxy_service(store: Annotated[RedisStore, Depends(get_store)]) -> ProxyService:
    return ProxyService(store, cooldown_seconds=get_settings().cooldown_seconds)


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
    response_format: Annotated[ProxyResponseFormat, Query(alias="format")] = "json",
) -> ProxyResponse | PlainTextResponse:
    proxy = await service.get_proxy(
        ProxyFilters(
            scheme=scheme,
            anonymity=anonymity,
            country=country,
            min_score=min_score,
        )
    )
    if proxy is None:
        raise HTTPException(status_code=404, detail="proxy not found")
    if response_format == "text":
        return PlainTextResponse(format_proxy_url(proxy, include_credentials=False))
    return ProxyResponse.from_endpoint(proxy)


@router.get("/proxy/list", response_model=ProxyListResponse)
async def list_proxies(
    service: Annotated[ProxyService, Depends(get_proxy_service)],
    pool: ProxyPool = "checked",
    scheme: ProxyScheme | None = None,
    anonymity: ProxyAnonymity | None = None,
    country: str | None = None,
    min_score: int | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ProxyListResponse:
    proxies = await service.list_proxies(
        pool=pool,
        filters=ProxyFilters(
            scheme=scheme,
            anonymity=anonymity,
            country=country,
            min_score=min_score,
        ),
        limit=limit,
        offset=offset,
    )
    responses = [ProxyResponse.from_endpoint(proxy) for proxy in proxies]
    return ProxyListResponse(proxies=responses, count=len(responses), limit=limit, offset=offset)


@router.post("/proxy/report", response_model=ReportProxyResponse)
async def report_proxy_result(
    report: ReportProxyRequest,
    service: Annotated[ProxyService, Depends(get_proxy_service)],
) -> ReportProxyResponse:
    proxy = await service.report_result(report)
    if proxy is None:
        raise HTTPException(status_code=404, detail="proxy not found")
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
) -> DeleteProxyResponse:
    deleted = await service.delete_proxy(proxy_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="proxy not found")
    return DeleteProxyResponse(proxy_id=proxy_id, deleted=True)
