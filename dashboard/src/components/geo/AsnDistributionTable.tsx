import { formatLatency, formatNumber } from "../../lib/format";
import type { GeoAsnSummary } from "../../types";

interface AsnDistributionTableProps {
  items: GeoAsnSummary[];
}

export function AsnDistributionTable({ items }: AsnDistributionTableProps) {
  return (
    <div className="table-shell">
      <table className="proxy-table compact-table">
        <thead>
          <tr>
            <th>ASN</th>
            <th>Total</th>
            <th>Elite</th>
            <th>Average latency</th>
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
