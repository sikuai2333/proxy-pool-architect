import { formatLatency, formatNumber } from "../../lib/format";
import type { GeoCountrySummary } from "../../types";

interface CountryDistributionChartProps {
  items: GeoCountrySummary[];
}

export function CountryDistributionChart({ items }: CountryDistributionChartProps) {
  const maxTotal = items[0]?.total ?? 1;

  return (
    <div className="stack-list">
      {items.map((item) => (
        <div key={item.country} className="stack-row">
          <div className="stack-row-header">
            <strong>{item.country}</strong>
            <span>
              {formatNumber(item.total)} total / {formatNumber(item.elite)} elite /{" "}
              {formatLatency(item.avg_latency_ms)}
            </span>
          </div>
          <div className="stack-track" aria-hidden="true">
            <div
              className="stack-fill"
              style={{ width: `${Math.max(8, Math.round((item.total / maxTotal) * 100))}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}
