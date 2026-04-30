from app.models.proxy import ProxyEndpoint


def serialize_proxy(proxy: ProxyEndpoint) -> str:
    return proxy.model_dump_json()


def deserialize_proxy(payload: str) -> ProxyEndpoint:
    return ProxyEndpoint.model_validate_json(payload)
