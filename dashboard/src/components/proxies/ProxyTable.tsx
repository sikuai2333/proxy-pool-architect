import { formatDateTime, formatLatency } from "../../lib/format";
import type { ProxyEndpoint } from "../../types";
import { AnonymityBadge } from "./AnonymityBadge";
import { ProxyStatusBadge } from "./ProxyStatusBadge";
import { SchemeBadge } from "./SchemeBadge";

interface ProxyTableProps {
  items: ProxyEndpoint[];
  onView: (proxy: ProxyEndpoint) => void;
  onDelete: (proxy: ProxyEndpoint) => void;
}

export function ProxyTable({ items, onView, onDelete }: ProxyTableProps) {
  return (
    <div className="table-shell">
      <table className="proxy-table">
        <thead>
          <tr>
            <th>Status</th>
            <th>Scheme</th>
            <th>Host</th>
            <th>Port</th>
            <th>Source</th>
            <th>Country</th>
            <th>ASN</th>
            <th>Anonymity</th>
            <th>Latency</th>
            <th>Score</th>
            <th>Success</th>
            <th>Fail</th>
            <th>Last checked</th>
            <th>Last error</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {items.map((proxy) => (
            <tr key={proxy.id}>
              <td>
                <ProxyStatusBadge status={proxy.status} />
              </td>
              <td>
                <SchemeBadge scheme={proxy.scheme} />
              </td>
              <td className="cell-strong">{proxy.host}</td>
              <td>{proxy.port}</td>
              <td className="cell-wrap">{proxy.source}</td>
              <td>{proxy.country || "Unknown"}</td>
              <td>{proxy.asn || "Unknown"}</td>
              <td>
                <AnonymityBadge anonymity={proxy.anonymity} />
              </td>
              <td>{formatLatency(proxy.latency_ms)}</td>
              <td>{proxy.score}</td>
              <td>{proxy.success_count}</td>
              <td>{proxy.fail_count}</td>
              <td>{formatDateTime(proxy.last_checked_at)}</td>
              <td className="cell-error">{proxy.last_error || "None"}</td>
              <td>
                <div className="table-actions">
                  <button className="button button-secondary" type="button" onClick={() => onView(proxy)}>
                    View
                  </button>
                  <button className="button button-danger" type="button" onClick={() => onDelete(proxy)}>
                    Delete
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
