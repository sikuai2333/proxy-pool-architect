import { useI18n } from "../../i18n";
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
  const { t, formatDateTime, formatLatency } = useI18n();

  return (
    <div className="table-shell">
      <table className="proxy-table">
        <thead>
          <tr>
            <th>{t("proxies.table.status")}</th>
            <th>{t("proxies.table.scheme")}</th>
            <th>{t("proxies.table.host")}</th>
            <th>{t("proxies.table.port")}</th>
            <th>{t("proxies.table.source")}</th>
            <th>{t("proxies.table.country")}</th>
            <th>ASN</th>
            <th>{t("proxies.table.anonymity")}</th>
            <th>{t("proxies.table.latency")}</th>
            <th>{t("proxies.table.score")}</th>
            <th>{t("proxies.table.success")}</th>
            <th>{t("proxies.table.fail")}</th>
            <th>{t("proxies.table.lastChecked")}</th>
            <th>{t("proxies.table.lastError")}</th>
            <th>{t("proxies.table.actions")}</th>
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
              <td>{proxy.country || t("common.unknown")}</td>
              <td>{proxy.asn || t("common.unknown")}</td>
              <td>
                <AnonymityBadge anonymity={proxy.anonymity} />
              </td>
              <td>{formatLatency(proxy.latency_ms)}</td>
              <td>{proxy.score}</td>
              <td>{proxy.success_count}</td>
              <td>{proxy.fail_count}</td>
              <td>{formatDateTime(proxy.last_checked_at)}</td>
              <td className="cell-error">{proxy.last_error || t("common.none")}</td>
              <td>
                <div className="table-actions">
                  <button className="button button-secondary" type="button" onClick={() => onView(proxy)}>
                    {t("common.view")}
                  </button>
                  <button className="button button-danger" type="button" onClick={() => onDelete(proxy)}>
                    {t("common.delete")}
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
