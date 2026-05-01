import type { ProxyPool } from "../../types";

interface ProxyStatusBadgeProps {
  status: ProxyPool;
}

export function ProxyStatusBadge({ status }: ProxyStatusBadgeProps) {
  return <span className={`badge badge-status badge-status-${status}`}>{status}</span>;
}
