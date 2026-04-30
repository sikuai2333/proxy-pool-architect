from app.models.proxy import ProxyEndpoint
from app.services.geo_service import GeoResolver


def test_geo_resolver_enriches_proxy_from_cidr_csv(tmp_path) -> None:
    geo_file = tmp_path / "geo.csv"
    geo_file.write_text(
        "cidr,country,asn\n1.2.3.0/24,US,AS64500\n",
        encoding="utf-8",
    )
    resolver = GeoResolver.from_csv(str(geo_file))
    proxy = ProxyEndpoint(
        id="http-1.2.3.4-8080",
        scheme="http",
        host="1.2.3.4",
        port=8080,
        source="test",
    )

    enriched = resolver.enrich(proxy)

    assert enriched.country == "US"
    assert enriched.asn == "AS64500"


def test_geo_resolver_ignores_domain_hosts(tmp_path) -> None:
    geo_file = tmp_path / "geo.csv"
    geo_file.write_text("cidr,country,asn\n1.2.3.0/24,US,AS64500\n", encoding="utf-8")
    resolver = GeoResolver.from_csv(str(geo_file))
    proxy = ProxyEndpoint(
        id="http-example.com-8080",
        scheme="http",
        host="example.com",
        port=8080,
        source="test",
    )

    assert resolver.enrich(proxy) == proxy
