import asyncio

from app.models.proxy import ProxyEndpoint, ProxyPool
from app.models.validation import ProxyValidationOutcome, ValidationResult
from app.services.scoring_service import apply_validation_score
from app.storage.redis_store import RedisStore
from app.validators.anonymity import AnonymityValidator
from app.validators.connectivity import ConnectivityValidator
from app.validators.protocol import ProtocolValidator


class ValidateService:
    def __init__(
        self,
        store: RedisStore,
        protocol_validator: ProtocolValidator,
        connectivity_validator: ConnectivityValidator,
        anonymity_validator: AnonymityValidator,
        concurrency: int = 100,
        min_elite_score: int = 80,
    ) -> None:
        self._store = store
        self._protocol_validator = protocol_validator
        self._connectivity_validator = connectivity_validator
        self._anonymity_validator = anonymity_validator
        self._semaphore = asyncio.Semaphore(concurrency)
        self._min_elite_score = min_elite_score

    async def validate_pool(
        self,
        pool: ProxyPool = "raw",
        limit: int = 100,
    ) -> list[ProxyValidationOutcome]:
        proxies = await self._store.list_proxies(pool, limit=limit, offset=0)
        return await asyncio.gather(
            *(self.validate_proxy(proxy, from_pool=pool) for proxy in proxies)
        )

    async def validate_proxy(
        self,
        proxy: ProxyEndpoint,
        from_pool: ProxyPool = "raw",
    ) -> ProxyValidationOutcome:
        async with self._semaphore:
            protocol = await self._protocol_validator.validate(proxy)
            connectivity: ValidationResult | None = None
            anonymity: ValidationResult | None = None

            if protocol.ok:
                connectivity = await self._connectivity_validator.validate(proxy)
            if connectivity is not None and connectivity.ok:
                anonymity = await self._anonymity_validator.validate(proxy)

            updated_proxy = apply_validation_score(proxy, protocol, connectivity, anonymity)
            target_pool = self._target_pool(updated_proxy, protocol, connectivity, anonymity)
            await self._store.remove_proxy(from_pool, proxy.id)
            stored_proxy = await self._store.add_proxy(target_pool, updated_proxy)

            return ProxyValidationOutcome(
                proxy_id=proxy.id,
                target_pool=target_pool,
                proxy=stored_proxy,
                protocol=protocol,
                connectivity=connectivity,
                anonymity=anonymity,
            )

    def _target_pool(
        self,
        proxy: ProxyEndpoint,
        protocol: ValidationResult,
        connectivity: ValidationResult | None,
        anonymity: ValidationResult | None,
    ) -> ProxyPool:
        if not protocol.ok or connectivity is None or not connectivity.ok:
            return "dead"
        if (
            anonymity is not None
            and anonymity.ok
            and anonymity.anonymity == "elite"
            and proxy.score >= self._min_elite_score
        ):
            return "elite"
        return "checked"
