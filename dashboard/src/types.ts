export type ProxyPool = "raw" | "checked" | "elite" | "dead" | "cooldown";
export type ProxyScheme = "http" | "https" | "socks4" | "socks5";
export type ProxyAnonymity = "unknown" | "transparent" | "anonymous" | "elite";

export interface ProxyEndpoint {
  id: string;
  scheme: ProxyScheme;
  host: string;
  port: number;
  auth_required?: boolean;
  username?: string | null;
  password?: string | null;
  source: string;
  country?: string | null;
  asn?: string | null;
  anonymity: ProxyAnonymity;
  latency_ms?: number | null;
  success_count: number;
  fail_count: number;
  consecutive_fail_count?: number;
  score: number;
  last_checked_at?: string | null;
  last_success_at?: string | null;
  last_error?: string | null;
  cooldown_until?: string | null;
  status: ProxyPool;
}

export interface DashboardStats {
  raw: number;
  checked: number;
  elite: number;
  dead: number;
  cooldown: number;
  avg_latency_ms: number | null;
  success_rate: number | null;
  last_fetch_at?: string | null;
  last_validate_at?: string | null;
  redis_status: "ok" | "error" | "unknown";
  scheduler_status: "running" | "stopped" | "unknown";
}

export interface HealthStatus {
  status: "ok" | "error" | "unknown";
  redis: "ok" | "error" | "unknown";
  scheduler: "running" | "stopped" | "unknown";
}

export interface OverviewData {
  stats: DashboardStats;
  health: HealthStatus;
}

export interface ProxyListQuery {
  pool?: ProxyPool;
  scheme?: ProxyScheme;
  anonymity?: ProxyAnonymity;
  country?: string;
  source?: string;
  min_score?: number;
  q?: string;
  limit?: number;
  offset?: number;
}

export interface ProxyListResponse {
  items: ProxyEndpoint[];
  total: number;
  limit: number;
  offset: number;
}

export interface ProxyFilterOptions {
  countries: string[];
  sources: string[];
}

export interface DeleteProxyResult {
  ok: boolean;
}

export interface GeoCountrySummary {
  country: string;
  total: number;
  elite: number;
  avg_latency_ms: number | null;
}

export interface GeoAsnSummary {
  asn: string;
  total: number;
  elite: number;
  avg_latency_ms: number | null;
}

export interface GeoSummary {
  countries: GeoCountrySummary[];
  asns: GeoAsnSummary[];
}

export interface ProviderSummary {
  name: string;
  enabled: boolean;
  last_fetch_at?: string | null;
  fetched_count: number;
  valid_count: number;
  last_error?: string | null;
}

export interface ValidationJob {
  id: string;
  started_at: string;
  finished_at?: string | null;
  checked_count: number;
  success_count: number;
  fail_count: number;
  timeout_count: number;
  status: "running" | "finished" | "failed";
}

export interface EventLogEntry {
  id: string;
  type: string;
  level: "info" | "warning" | "error";
  message: string;
  created_at: string;
}

export interface SafeNetworkingSettings {
  authorized_targets_only: boolean;
  block_private_networks: boolean;
  mask_proxy_credentials: boolean;
}

export interface DashboardSettings {
  fetch_interval_seconds: number;
  validate_interval_seconds: number;
  validate_timeout_seconds: number;
  validate_concurrency: number;
  min_elite_score: number;
  cooldown_seconds: number;
  safe_networking: SafeNetworkingSettings;
}

export type DashboardRoute =
  | "overview"
  | "proxies"
  | "providers"
  | "geo"
  | "validation"
  | "logs"
  | "settings";

export interface NavigationItem {
  route: DashboardRoute;
  label: string;
}
