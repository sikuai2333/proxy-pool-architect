import { formatDateTime, formatNumber } from "../../lib/format";
import type { ProviderSummary } from "../../types";

interface ProviderTableProps {
  items: ProviderSummary[];
}

export function ProviderTable({ items }: ProviderTableProps) {
  return (
    <div className="table-shell">
      <table className="proxy-table compact-table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Status</th>
            <th>Last fetch</th>
            <th>Fetched count</th>
            <th>Valid count</th>
            <th>Error summary</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={item.name}>
              <td className="cell-strong cell-wrap">{item.name}</td>
              <td>
                <span className={item.enabled ? "badge badge-status badge-status-elite" : "badge"}>
                  {item.enabled ? "enabled" : "disabled"}
                </span>
              </td>
              <td>{formatDateTime(item.last_fetch_at)}</td>
              <td>{formatNumber(item.fetched_count)}</td>
              <td>{formatNumber(item.valid_count)}</td>
              <td className="cell-error">{item.last_error || "None"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
