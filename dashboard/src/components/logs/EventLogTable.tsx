import { useI18n, type TranslationKey } from "../../i18n";
import type { EventLogEntry } from "../../types";

interface EventLogTableProps {
  items: EventLogEntry[];
}

export function EventLogTable({ items }: EventLogTableProps) {
  const { t, formatDateTime } = useI18n();

  return (
    <div className="table-shell">
      <table className="proxy-table compact-table">
        <caption className="sr-only">{t("logs.tableCaption")}</caption>
        <thead>
          <tr>
            <th scope="col">{t("logs.time")}</th>
            <th scope="col">{t("logs.level")}</th>
            <th scope="col">{t("logs.type")}</th>
            <th scope="col">{t("logs.message")}</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={item.id}>
              <td>{formatDateTime(item.created_at)}</td>
              <td>
                <span className={`badge ${item.level === "error" ? "badge-status-dead" : item.level === "warning" ? "badge-status-cooldown" : "badge-status-checked"}`}>
                  {t(`eventLevel.${item.level}` as TranslationKey)}
                </span>
              </td>
              <td className="cell-wrap">{item.type}</td>
              <td className="cell-error">{item.message}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
