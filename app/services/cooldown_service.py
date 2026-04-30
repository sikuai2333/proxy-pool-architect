from datetime import UTC, datetime

from app.models.proxy import ProxyEndpoint
from app.storage.redis_store import RedisStore
from app.utils.time import parse_utc_datetime


class CooldownService:
    def __init__(self, store: RedisStore) -> None:
        self._store = store

    async def release_expired(self, limit: int = 1000) -> list[ProxyEndpoint]:
        now = datetime.now(UTC)
        proxies = await self._store.list_proxies("cooldown", limit=limit, offset=0)
        released: list[ProxyEndpoint] = []
        for proxy in proxies:
            if self._is_expired(proxy, now):
                await self._store.remove_proxy("cooldown", proxy.id)
                released.append(
                    await self._store.add_proxy(
                        "raw",
                        proxy.model_copy(update={"cooldown_until": None}),
                    )
                )
        return released

    @staticmethod
    def _is_expired(proxy: ProxyEndpoint, now: datetime) -> bool:
        if proxy.cooldown_until is None:
            return True
        return parse_utc_datetime(proxy.cooldown_until) <= now
