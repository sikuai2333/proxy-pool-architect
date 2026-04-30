from app.models.proxy import ProxyEndpoint
from app.models.validation import ValidationResult
from app.utils.proxy_url import SUPPORTED_PROXY_SCHEMES
from app.validators.base import ProxyValidator


class ProtocolValidator(ProxyValidator):
    async def validate(self, proxy: ProxyEndpoint) -> ValidationResult:
        if proxy.scheme not in SUPPORTED_PROXY_SCHEMES:
            return ValidationResult(
                validator="protocol",
                ok=False,
                error="unsupported_proxy_scheme",
            )
        if not proxy.host:
            return ValidationResult(
                validator="protocol",
                ok=False,
                error="missing_proxy_host",
            )
        if proxy.port < 1 or proxy.port > 65535:
            return ValidationResult(
                validator="protocol",
                ok=False,
                error="invalid_proxy_port",
            )
        return ValidationResult(validator="protocol", ok=True)
