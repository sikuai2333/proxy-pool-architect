from datetime import UTC, datetime, timedelta


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def utc_plus_seconds_iso(seconds: int) -> str:
    return (datetime.now(UTC) + timedelta(seconds=seconds)).isoformat()


def parse_utc_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)
