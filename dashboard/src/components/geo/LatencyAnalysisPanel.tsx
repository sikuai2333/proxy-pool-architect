import { EmptyState } from "../common/EmptyState";
import { useI18n } from "../../i18n";
import type { GeoAsnSummary, GeoCountrySummary } from "../../types";

interface LatencyAnalysisPanelProps {
  countries: GeoCountrySummary[];
  asns: GeoAsnSummary[];
}

interface LatencyGroup {
  scope: "country" | "asn";
  name: string;
  total: number;
  elite: number;
  avgLatencyMs: number;
}

function buildLatencyGroups(countries: GeoCountrySummary[], asns: GeoAsnSummary[]) {
  const countryGroups: LatencyGroup[] = countries
    .filter((item) => item.avg_latency_ms != null)
    .map((item) => ({
      scope: "country",
      name: item.country,
      total: item.total,
      elite: item.elite,
      avgLatencyMs: item.avg_latency_ms as number
    }));

  const asnGroups: LatencyGroup[] = asns
    .filter((item) => item.avg_latency_ms != null)
    .map((item) => ({
      scope: "asn",
      name: item.asn,
      total: item.total,
      elite: item.elite,
      avgLatencyMs: item.avg_latency_ms as number
    }));

  return [...countryGroups, ...asnGroups].sort((left, right) => left.avgLatencyMs - right.avgLatencyMs);
}

interface LatencyTableProps {
  title: string;
  rows: LatencyGroup[];
}

function LatencyTable({ title, rows }: LatencyTableProps) {
  const { t, formatLatency, formatNumber } = useI18n();

  return (
    <div className="latency-table-block">
      <h3>{title}</h3>
      <div className="table-shell">
        <table className="proxy-table compact-table latency-table">
          <caption className="sr-only">{t("geo.latencyTableCaption", { title })}</caption>
          <thead>
            <tr>
              <th scope="col">{t("geo.scope")}</th>
              <th scope="col">{t("geo.group")}</th>
              <th scope="col">{t("geo.averageLatency")}</th>
              <th scope="col">{t("geo.total")}</th>
              <th scope="col">{t("geo.elite")}</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((item) => (
              <tr key={`${item.scope}-${item.name}`}>
                <td>{item.scope === "country" ? t("geo.countryScope") : t("geo.asnScope")}</td>
                <td className="cell-strong">{item.name}</td>
                <td>{formatLatency(item.avgLatencyMs)}</td>
                <td>{formatNumber(item.total)}</td>
                <td>{formatNumber(item.elite)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export function LatencyAnalysisPanel({ countries, asns }: LatencyAnalysisPanelProps) {
  const { t } = useI18n();
  const rows = buildLatencyGroups(countries, asns);

  if (rows.length === 0) {
    return <EmptyState title={t("geo.noLatencyTitle")} message={t("geo.noLatencyMessage")} />;
  }

  const fastest = rows.slice(0, 5);
  const slowest = [...rows].reverse().slice(0, 5);

  return (
    <div className="latency-analysis-grid">
      <LatencyTable title={t("geo.lowestLatency")} rows={fastest} />
      <LatencyTable title={t("geo.highestLatency")} rows={slowest} />
    </div>
  );
}
