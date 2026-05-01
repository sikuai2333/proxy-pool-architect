from app.models.proxy import ProxyPool

POOL_NAMES: tuple[ProxyPool, ...] = ("raw", "checked", "elite", "dead", "cooldown")
SELECTION_POOLS: tuple[ProxyPool, ...] = ("elite", "checked")


def all_proxy_index_key() -> str:
    return "proxy:index:all"


def proxy_key(pool: ProxyPool, proxy_id: str) -> str:
    return f"proxy:{pool}:{proxy_id}"


def pool_index_key(pool: ProxyPool) -> str:
    return f"proxy:index:{pool}"


def proxy_attribute_index_key(field: str, value: str) -> str:
    return f"proxy:index:{field}:{value.casefold()}"


def proxy_pool_key(proxy_id: str) -> str:
    return f"proxy:pool:{proxy_id}"


def session_proxy_key(session_id: str) -> str:
    return f"proxy:session:{session_id}"


def admin_session_key(token: str) -> str:
    return f"auth:session:{token}"


def proxy_list_cache_index_key() -> str:
    return "proxy:cache:list:index"


def proxy_list_cache_key(signature: str) -> str:
    return f"proxy:cache:list:{signature}"
