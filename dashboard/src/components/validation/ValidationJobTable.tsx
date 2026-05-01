import { useI18n, type TranslationKey } from "../../i18n";
import type { ValidationJob } from "../../types";

interface ValidationJobTableProps {
  items: ValidationJob[];
}

export function ValidationJobTable({ items }: ValidationJobTableProps) {
  const { t, formatDateTime, formatNumber, formatPercent } = useI18n();

  return (
    <div className="table-shell">
      <table className="proxy-table compact-table">
        <caption className="sr-only">{t("validation.tableCaption")}</caption>
        <thead>
          <tr>
            <th scope="col">{t("validation.job")}</th>
            <th scope="col">{t("providers.status")}</th>
            <th scope="col">{t("validation.started")}</th>
            <th scope="col">{t("validation.finished")}</th>
            <th scope="col">{t("validation.checked")}</th>
            <th scope="col">{t("proxies.table.success")}</th>
            <th scope="col">{t("proxies.table.fail")}</th>
            <th scope="col">{t("validation.timeout")}</th>
            <th scope="col">{t("overview.successRate")}</th>
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
                    {t(`validationStatus.${item.status}` as TranslationKey)}
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
