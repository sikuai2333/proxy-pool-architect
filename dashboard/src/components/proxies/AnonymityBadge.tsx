import { useI18n, type TranslationKey } from "../../i18n";
import type { ProxyAnonymity } from "../../types";

interface AnonymityBadgeProps {
  anonymity: ProxyAnonymity;
}

export function AnonymityBadge({ anonymity }: AnonymityBadgeProps) {
  const { t } = useI18n();
  const labelKey = `anonymity.${anonymity}` as TranslationKey;

  return <span className={`badge badge-anonymity badge-anonymity-${anonymity}`}>{t(labelKey)}</span>;
}
