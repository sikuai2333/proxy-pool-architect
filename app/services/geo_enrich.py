"""Retroactively enrich existing proxies with GeoIP data."""

import asyncio

from loguru import logger

from app.services.geo_service import GeoResolver
from app.storage.sqlite_store import SQLiteStore


async def enrich_existing_proxies(store: SQLiteStore, resolver: GeoResolver) -> int:
    """Update all proxies in the database with GeoIP country/ASN data.

    Runs in batches to avoid blocking the event loop.
    Returns the number of proxies that were updated.
    """
    proxies = await store.list_all_proxies()
    updated = 0
    batch_size = 200

    for i in range(0, len(proxies), batch_size):
        batch = proxies[i : i + batch_size]
        for proxy in batch:
            if proxy.country is not None:
                continue
            enriched = resolver.enrich(proxy)
            if enriched.country is not None:
                pool = await store.find_proxy_pool(proxy.id)
                if pool is not None:
                    await store.save_proxy(pool, enriched)
                    updated += 1

        # Yield control every batch so other tasks can run
        await asyncio.sleep(0)

    if updated > 0:
        logger.info("GeoIP retroactively enriched {} proxies", updated)
    return updated


async def enrich_in_background(store: SQLiteStore, resolver: GeoResolver) -> None:
    """Run GeoIP enrichment in the background without blocking startup."""
    try:
        await enrich_existing_proxies(store, resolver)
    except Exception as exc:
        logger.warning("Background GeoIP enrichment failed: {}", exc)
