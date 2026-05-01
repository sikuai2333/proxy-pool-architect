export function formatNumber(value: number) {
  return new Intl.NumberFormat("en-US").format(value);
}

export function formatLatency(value: number | null | undefined) {
  return value == null ? "Unknown" : `${formatNumber(value)} ms`;
}

export function formatPercent(value: number | null | undefined) {
  return value == null ? "Unknown" : `${Math.round(value * 100)}%`;
}

export function formatDateTime(value?: string | null) {
  if (!value) {
    return "Unknown";
  }

  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit"
  }).format(new Date(value));
}

export function maskCredential(value?: string | null) {
  if (!value) {
    return "Not set";
  }

  if (value.length <= 2) {
    return "**";
  }

  return `${value.slice(0, 2)}***`;
}
