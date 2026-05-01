import { useI18n } from "../../i18n";
import type { GeoCountrySummary } from "../../types";

interface CountryDistributionChartProps {
  items: GeoCountrySummary[];
}

export function CountryDistributionChart({ items }: CountryDistributionChartProps) {
  const { t, formatLatency, formatNumber } = useI18n();
  const maxTotal = items[0]?.total ?? 1;

  return (
    <div className="stack-list" role="list">
      {items.map((item) => (
        <div key={item.country} className="stack-row" role="listitem">
          <div className="stack-row-header">
            <strong>{item.country}</strong>
            <span>
              {t("geo.stackSummary", {
                total: formatNumber(item.total),
                elite: formatNumber(item.elite),
                latency: formatLatency(item.avg_latency_ms)
              })}
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
