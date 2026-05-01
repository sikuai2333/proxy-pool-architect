import type { ProxyScheme } from "../../types";

interface SchemeBadgeProps {
  scheme: ProxyScheme;
}

export function SchemeBadge({ scheme }: SchemeBadgeProps) {
  return <span className={`badge badge-scheme badge-scheme-${scheme}`}>{scheme}</span>;
}
