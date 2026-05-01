import { useI18n } from "../../i18n";
import type { GeoAsnSummary } from "../../types";

interface AsnDistributionTableProps {
  items: GeoAsnSummary[];
}

export function AsnDistributionTable({ items }: AsnDistributionTableProps) {
  const { t, formatLatency, formatNumber } = useI18n();

  return (
    <div className="table-shell">
      <table className="proxy-table compact-table">
        <caption className="sr-only">{t("geo.asnTableCaption")}</caption>
        <thead>
          <tr>
            <th scope="col">ASN</th>
            <th scope="col">{t("geo.total")}</th>
            <th scope="col">{t("geo.elite")}</th>
            <th scope="col">{t("geo.averageLatency")}</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={item.asn}>
              <td className="cell-strong">{item.asn}</td>
              <td>{formatNumber(item.total)}</td>
              <td>{formatNumber(item.elite)}</td>
              <td>{formatLatency(item.avg_latency_ms)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
