import { useI18n } from "../../i18n";
import type { ProviderSummary } from "../../types";

interface ProviderTableProps {
  items: ProviderSummary[];
}

export function ProviderTable({ items }: ProviderTableProps) {
  const { t, formatDateTime, formatNumber } = useI18n();

  return (
    <div className="table-shell">
      <table className="proxy-table compact-table">
        <caption className="sr-only">{t("providers.tableCaption")}</caption>
        <thead>
          <tr>
            <th scope="col">{t("providers.name")}</th>
            <th scope="col">{t("providers.status")}</th>
            <th scope="col">{t("providers.lastFetch")}</th>
            <th scope="col">{t("providers.fetchedCount")}</th>
            <th scope="col">{t("providers.validCount")}</th>
            <th scope="col">{t("providers.errorSummary")}</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={item.name}>
              <td className="cell-strong cell-wrap">{item.name}</td>
              <td>
                <span className={item.enabled ? "badge badge-status badge-status-elite" : "badge"}>
                  {item.enabled ? t("provider.enabled") : t("provider.disabled")}
                </span>
              </td>
              <td>{formatDateTime(item.last_fetch_at)}</td>
              <td>{formatNumber(item.fetched_count)}</td>
              <td>{formatNumber(item.valid_count)}</td>
              <td className="cell-error">{item.last_error || t("common.none")}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
