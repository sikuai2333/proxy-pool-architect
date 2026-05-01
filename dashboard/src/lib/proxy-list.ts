import type { ProxyEndpoint, ProxyFilterOptions, ProxyListQuery } from "../types";

export function filterAndSortProxies(items: ProxyEndpoint[], query: ProxyListQuery) {
  return items
    .filter((proxy) => (query.pool ? proxy.status === query.pool : true))
    .filter((proxy) => (query.scheme ? proxy.scheme === query.scheme : true))
    .filter((proxy) => (query.anonymity ? proxy.anonymity === query.anonymity : true))
    .filter((proxy) => (query.country ? proxy.country === query.country : true))
    .filter((proxy) => (query.source ? proxy.source === query.source : true))
    .filter((proxy) => (query.min_score != null ? proxy.score >= query.min_score : true))
    .filter((proxy) => {
      if (!query.q) {
        return true;
      }

      const needle = query.q.trim().toLowerCase();
      return proxy.host.toLowerCase().includes(needle) || proxy.id.toLowerCase().includes(needle);
    })
    .sort((left, right) => {
      if (right.score !== left.score) {
        return right.score - left.score;
      }

      const leftTime = left.last_checked_at ? Date.parse(left.last_checked_at) : 0;
      const rightTime = right.last_checked_at ? Date.parse(right.last_checked_at) : 0;
      return rightTime - leftTime;
    });
}

export function collectProxyFilterOptions(items: ProxyEndpoint[]): ProxyFilterOptions {
  const countries = [
    ...new Set(items.map((proxy) => proxy.country).filter((country): country is string => Boolean(country)))
  ];
  const sources = [...new Set(items.map((proxy) => proxy.source))];

  return {
    countries: countries.sort(),
    sources: sources.sort()
  };
}
