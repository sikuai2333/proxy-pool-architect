from app.models.proxy import ProxyPool

POOL_NAMES: tuple[ProxyPool, ...] = ("raw", "checked", "elite", "dead", "cooldown")
SELECTION_POOLS: tuple[ProxyPool, ...] = ("elite", "checked")


def proxy_key(pool: ProxyPool, proxy_id: str) -> str:
    return f"proxy:{pool}:{proxy_id}"


def pool_index_key(pool: ProxyPool) -> str:
    return f"proxy:index:{pool}"


def proxy_pool_key(proxy_id: str) -> str:
    return f"proxy:pool:{proxy_id}"
