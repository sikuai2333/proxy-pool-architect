import type {
  GeoAsnSummary,
  GeoCountrySummary,
  GeoSummary,
  ProviderSummary,
  ProxyEndpoint
} from "../types";

function averageLatency(values: Array<number | null | undefined>) {
  const latencies = values.filter((value): value is number => value != null);
  if (latencies.length === 0) {
    return null;
  }

  const total = latencies.reduce((sum, value) => sum + value, 0);
  return Math.round(total / latencies.length);
}

export function deriveGeoSummary(items: ProxyEndpoint[]): GeoSummary {
  const countryBuckets = new Map<string, ProxyEndpoint[]>();
  const asnBuckets = new Map<string, ProxyEndpoint[]>();

  items.forEach((item) => {
    const country = item.country || "Unknown";
    const asn = item.asn || "Unknown";

    const countryItems = countryBuckets.get(country) ?? [];
    countryItems.push(item);
    countryBuckets.set(country, countryItems);

    const asnItems = asnBuckets.get(asn) ?? [];
    asnItems.push(item);
    asnBuckets.set(asn, asnItems);
  });

  const countries: GeoCountrySummary[] = [...countryBuckets.entries()]
    .map(([country, bucket]) => ({
      country,
      total: bucket.length,
      elite: bucket.filter((item) => item.status === "elite").length,
      avg_latency_ms: averageLatency(bucket.map((item) => item.latency_ms))
    }))
    .sort((left, right) => right.total - left.total);

  const asns: GeoAsnSummary[] = [...asnBuckets.entries()]
    .map(([asn, bucket]) => ({
      asn,
      total: bucket.length,
      elite: bucket.filter((item) => item.status === "elite").length,
      avg_latency_ms: averageLatency(bucket.map((item) => item.latency_ms))
    }))
    .sort((left, right) => right.total - left.total);

  return { countries, asns };
}

export function deriveProviderSummaries(items: ProxyEndpoint[]): ProviderSummary[] {
  const buckets = new Map<string, ProxyEndpoint[]>();

  items.forEach((item) => {
    const group = buckets.get(item.source) ?? [];
    group.push(item);
    buckets.set(item.source, group);
  });

  return [...buckets.entries()]
    .map(([name, bucket]) => {
      const lastFetchAt = bucket
        .map((item) => item.last_checked_at || item.last_success_at || null)
        .filter((value): value is string => Boolean(value))
        .sort()
        .at(-1);
      const lastErrors = bucket
        .map((item) => item.last_error)
        .filter((value): value is string => Boolean(value));

      return {
        name,
        enabled: true,
        last_fetch_at: lastFetchAt ?? null,
        fetched_count: bucket.length,
        valid_count: bucket.filter((item) => item.status === "checked" || item.status === "elite").length,
        last_error: lastErrors.at(0) ?? null
      };
    })
    .sort((left, right) => right.valid_count - left.valid_count || right.fetched_count - left.fetched_count);
}
