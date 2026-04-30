import csv
from dataclasses import dataclass
from ipaddress import IPv4Network, IPv6Network, ip_address, ip_network
from pathlib import Path

from app.core.config import Settings
from app.models.proxy import ProxyEndpoint


@dataclass(frozen=True)
class GeoRecord:
    network: IPv4Network | IPv6Network
    country: str | None
    asn: str | None


class GeoResolver:
    def __init__(self, records: list[GeoRecord]) -> None:
        self._records = sorted(
            records,
            key=lambda record: getattr(record.network, "prefixlen", 0),
            reverse=True,
        )

    @classmethod
    def from_settings(cls, settings: Settings) -> "GeoResolver | None":
        if not settings.geo_enabled:
            return None
        return cls.from_csv(settings.geo_file)

    @classmethod
    def from_csv(cls, path: str) -> "GeoResolver":
        geo_path = Path(path)
        if not geo_path.exists():
            return cls([])

        records: list[GeoRecord] = []
        with geo_path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                cidr = row.get("cidr")
                if not cidr:
                    continue
                records.append(
                    GeoRecord(
                        network=ip_network(cidr, strict=False),
                        country=_empty_to_none(row.get("country")),
                        asn=_empty_to_none(row.get("asn")),
                    )
                )
        return cls(records)

    def enrich(self, proxy: ProxyEndpoint) -> ProxyEndpoint:
        try:
            host_ip = ip_address(proxy.host)
        except ValueError:
            return proxy

        for record in self._records:
            if host_ip in record.network:
                return proxy.model_copy(update={"country": record.country, "asn": record.asn})
        return proxy


def _empty_to_none(value: str | None) -> str | None:
    if value is None or value == "":
        return None
    return value
