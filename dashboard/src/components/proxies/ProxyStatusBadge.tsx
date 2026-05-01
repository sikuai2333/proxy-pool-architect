import { useI18n, type TranslationKey } from "../../i18n";
import type { ProxyPool } from "../../types";

interface ProxyStatusBadgeProps {
  status: ProxyPool;
}

export function ProxyStatusBadge({ status }: ProxyStatusBadgeProps) {
  const { t } = useI18n();
  const labelKey = `proxyPool.${status}` as TranslationKey;

  return <span className={`badge badge-status badge-status-${status}`}>{t(labelKey)}</span>;
}
