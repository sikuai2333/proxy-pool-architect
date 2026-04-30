from app.models.proxy import ProxyEndpoint
from app.models.validation import ValidationResult
from app.utils.time import utc_now_iso

INITIAL_SCORE = 50


def apply_validation_score(
    proxy: ProxyEndpoint,
    protocol: ValidationResult,
    connectivity: ValidationResult | None,
    anonymity: ValidationResult | None,
) -> ProxyEndpoint:
    now = utc_now_iso()
    score = _starting_score(proxy)
    score += _validation_delta(protocol, connectivity, anonymity)

    connectivity_ok = connectivity is not None and connectivity.ok
    fail_count = proxy.fail_count if connectivity_ok else proxy.fail_count + 1
    consecutive_fail_count = 0 if connectivity_ok else proxy.consecutive_fail_count + 1
    success_count = proxy.success_count + 1 if connectivity_ok else proxy.success_count
    last_error = None if connectivity_ok else _first_error(protocol, connectivity)

    updates: dict[str, object] = {
        "score": score,
        "success_count": success_count,
        "fail_count": fail_count,
        "consecutive_fail_count": consecutive_fail_count,
        "last_checked_at": now,
        "last_error": last_error,
    }

    if connectivity is not None and connectivity.latency_ms is not None:
        updates["latency_ms"] = connectivity.latency_ms
    if connectivity_ok:
        updates["last_success_at"] = now
    if anonymity is not None and anonymity.anonymity is not None:
        updates["anonymity"] = anonymity.anonymity

    return proxy.model_copy(update=updates)


def _starting_score(proxy: ProxyEndpoint) -> int:
    if proxy.score == 0 and proxy.success_count == 0 and proxy.fail_count == 0:
        return INITIAL_SCORE
    return proxy.score


def _validation_delta(
    protocol: ValidationResult,
    connectivity: ValidationResult | None,
    anonymity: ValidationResult | None,
) -> int:
    delta = 0
    if not protocol.ok:
        delta -= 20
        return delta

    if connectivity is not None and connectivity.ok:
        delta += 10
        delta += _latency_delta(connectivity.latency_ms)
    else:
        delta -= 20

    if anonymity is not None and anonymity.ok:
        if anonymity.anonymity == "elite":
            delta += 30
        elif anonymity.anonymity == "anonymous":
            delta += 15
        elif anonymity.anonymity == "transparent":
            delta -= 50

    return delta


def _latency_delta(latency_ms: int | None) -> int:
    if latency_ms is None:
        return 0
    if latency_ms < 500:
        return 10
    if latency_ms <= 1500:
        return 5
    if latency_ms > 5000:
        return -15
    return 0


def _first_error(
    protocol: ValidationResult,
    connectivity: ValidationResult | None,
) -> str | None:
    if not protocol.ok:
        return protocol.error
    if connectivity is not None and not connectivity.ok:
        return connectivity.error
    return None
