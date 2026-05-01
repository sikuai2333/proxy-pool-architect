import { formatDateTime, formatNumber, formatPercent } from "../../lib/format";
import type { ValidationJob } from "../../types";

interface ValidationJobTableProps {
  items: ValidationJob[];
}

export function ValidationJobTable({ items }: ValidationJobTableProps) {
  return (
    <div className="table-shell">
      <table className="proxy-table compact-table">
        <thead>
          <tr>
            <th>Job</th>
            <th>Status</th>
            <th>Started</th>
            <th>Finished</th>
            <th>Checked</th>
            <th>Success</th>
            <th>Fail</th>
            <th>Timeout</th>
            <th>Success rate</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => {
            const successRate = item.checked_count > 0 ? item.success_count / item.checked_count : null;

            return (
              <tr key={item.id}>
                <td className="cell-strong">{item.id}</td>
                <td>
                  <span className={`badge ${item.status === "finished" ? "badge-status-checked" : "badge-status-cooldown"}`}>
                    {item.status}
                  </span>
                </td>
                <td>{formatDateTime(item.started_at)}</td>
                <td>{formatDateTime(item.finished_at)}</td>
                <td>{formatNumber(item.checked_count)}</td>
                <td>{formatNumber(item.success_count)}</td>
                <td>{formatNumber(item.fail_count)}</td>
                <td>{formatNumber(item.timeout_count)}</td>
                <td>{formatPercent(successRate)}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
