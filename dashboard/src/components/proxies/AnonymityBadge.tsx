import type { ProxyAnonymity } from "../../types";

interface AnonymityBadgeProps {
  anonymity: ProxyAnonymity;
}

export function AnonymityBadge({ anonymity }: AnonymityBadgeProps) {
  return <span className={`badge badge-anonymity badge-anonymity-${anonymity}`}>{anonymity}</span>;
}
