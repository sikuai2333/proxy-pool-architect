import type {
  AuthSessionStatus,
  DashboardStats,
  DashboardSettings,
  DeleteProxyResult,
  EventLogEntry,
  GeoSummary,
  HealthStatus,
  OverviewData,
  ProviderSummary,
  ProxyEndpoint,
  ProxyFilterOptions,
  PaginatedResponse,
  ProxyUrlImportFileType,
  ProxyUrlImportResult,
  ProxyListQuery,
  ProxyListResponse,
  ValidationJob
} from "../types";
import { deriveGeoSummary, deriveProviderSummaries } from "./dashboard-derive";
import { collectProxyFilterOptions, filterAndSortProxies } from "./proxy-list";

const now = () => new Date().toISOString();

export const mockStats: DashboardStats = {
  raw: 1280,
  checked: 342,
  elite: 76,
  dead: 862,
  cooldown: 18,
  avg_latency_ms: 1240,
  success_rate: 0.72,
  last_fetch_at: now(),
  last_validate_at: now(),
  db_status: "ok",
  scheduler_status: "running"
};

export const mockHealth: HealthStatus = {
  status: "ok",
  db: "ok",
  scheduler: "running"
};

const mockAuthSession: AuthSessionStatus = {
  enabled: false,
  authenticated: false,
  username: null,
  expires_at: null,
  auth_method: "disabled"
};

function createProxyId(scheme: string, host: string, port: number) {
  return `${scheme}-${host}-${port}`;
}

function hoursAgo(hours: number) {
  return new Date(Date.now() - hours * 60 * 60 * 1000).toISOString();
}

function createMockProxy(
  proxy: Omit<ProxyEndpoint, "id"> & { id?: string }
): ProxyEndpoint {
  return {
    ...proxy,
    auth_required: proxy.auth_required ?? Boolean(proxy.username || proxy.password),
    id: proxy.id ?? createProxyId(proxy.scheme, proxy.host, proxy.port)
  };
}

function cloneProxy(proxy: ProxyEndpoint): ProxyEndpoint {
  return { ...proxy };
}

function buildMockProxyStore(): ProxyEndpoint[] {
  return [
    createMockProxy({
      scheme: "socks5",
      host: "1.2.3.4",
      port: 1080,
      username: "svc-east",
      password: "secret-east",
      source: "core_adapter:mihomo",
      country: "US",
      asn: "AS12345",
      anonymity: "elite",
      latency_ms: 820,
      success_count: 12,
      fail_count: 1,
      score: 91,
      last_checked_at: hoursAgo(1),
      last_success_at: hoursAgo(1),
      last_error: null,
      status: "elite"
    }),
    createMockProxy({
      scheme: "http",
      host: "8.8.4.2",
      port: 8080,
      source: "url_list_provider",
      country: "DE",
      asn: "AS3320",
      anonymity: "anonymous",
      latency_ms: 1130,
      success_count: 16,
      fail_count: 3,
      score: 79,
      last_checked_at: hoursAgo(2),
      last_success_at: hoursAgo(2),
      last_error: null,
      status: "checked"
    }),
    createMockProxy({
      scheme: "https",
      host: "34.76.12.10",
      port: 8443,
      source: "static_provider",
      country: "SG",
      asn: "AS15169",
      anonymity: "elite",
      latency_ms: 640,
      success_count: 28,
      fail_count: 0,
      score: 95,
      last_checked_at: hoursAgo(3),
      last_success_at: hoursAgo(3),
      last_error: null,
      status: "elite"
    }),
    createMockProxy({
      scheme: "socks4",
      host: "77.91.72.8",
      port: 9050,
      source: "tor",
      country: "NL",
      asn: "AS60781",
      anonymity: "anonymous",
      latency_ms: 1580,
      success_count: 8,
      fail_count: 6,
      score: 58,
      last_checked_at: hoursAgo(4),
      last_success_at: hoursAgo(5),
      last_error: "High latency during validation",
      status: "checked"
    }),
    createMockProxy({
      scheme: "http",
      host: "103.44.19.7",
      port: 8000,
      source: "url_list_provider",
      country: "JP",
      asn: "AS2516",
      anonymity: "unknown",
      latency_ms: null,
      success_count: 0,
      fail_count: 0,
      score: 50,
      last_checked_at: null,
      last_success_at: null,
      last_error: null,
      status: "raw"
    }),
    createMockProxy({
      scheme: "socks5",
      host: "61.19.42.200",
      port: 1080,
      source: "clash_subscription",
      country: "HK",
      asn: "AS9304",
      anonymity: "elite",
      latency_ms: 540,
      success_count: 34,
      fail_count: 2,
      score: 96,
      last_checked_at: hoursAgo(2),
      last_success_at: hoursAgo(2),
      last_error: null,
      status: "elite"
    }),
    createMockProxy({
      scheme: "https",
      host: "45.90.12.77",
      port: 443,
      source: "paid_provider",
      country: "GB",
      asn: "AS9009",
      anonymity: "elite",
      latency_ms: 720,
      success_count: 41,
      fail_count: 2,
      score: 98,
      last_checked_at: hoursAgo(1),
      last_success_at: hoursAgo(1),
      last_error: null,
      status: "elite"
    }),
    createMockProxy({
      scheme: "http",
      host: "172.16.1.11",
      port: 8081,
      source: "static_provider",
      country: "US",
      asn: "AS7922",
      anonymity: "transparent",
      latency_ms: 2410,
      success_count: 4,
      fail_count: 11,
      score: 21,
      last_checked_at: hoursAgo(1),
      last_success_at: hoursAgo(12),
      last_error: "Forwarded header leaked client address",
      status: "dead"
    }),
    createMockProxy({
      scheme: "socks5",
      host: "210.5.31.18",
      port: 1080,
      source: "core_adapter:sing-box",
      country: "KR",
      asn: "AS4766",
      anonymity: "elite",
      latency_ms: 690,
      success_count: 21,
      fail_count: 1,
      score: 89,
      last_checked_at: hoursAgo(6),
      last_success_at: hoursAgo(6),
      last_error: null,
      status: "checked"
    }),
    createMockProxy({
      scheme: "http",
      host: "91.223.82.16",
      port: 3128,
      source: "url_list_provider",
      country: "FR",
      asn: "AS3215",
      anonymity: "anonymous",
      latency_ms: 1360,
      success_count: 10,
      fail_count: 4,
      score: 67,
      last_checked_at: hoursAgo(7),
      last_success_at: hoursAgo(8),
      last_error: null,
      status: "checked"
    }),
    createMockProxy({
      scheme: "socks4",
      host: "185.14.31.90",
      port: 1088,
      source: "freeproxy_provider",
      country: "SE",
      asn: "AS12552",
      anonymity: "unknown",
      latency_ms: null,
      success_count: 0,
      fail_count: 0,
      score: 52,
      last_checked_at: null,
      last_success_at: null,
      last_error: null,
      status: "raw"
    }),
    createMockProxy({
      scheme: "http",
      host: "203.0.113.40",
      port: 8080,
      source: "url_list_provider",
      country: "IN",
      asn: "AS4755",
      anonymity: "anonymous",
      latency_ms: 1880,
      success_count: 7,
      fail_count: 5,
      score: 54,
      last_checked_at: hoursAgo(5),
      last_success_at: hoursAgo(10),
      last_error: "Timeout while reaching test URL",
      status: "cooldown"
    }),
    createMockProxy({
      scheme: "https",
      host: "198.51.100.20",
      port: 9443,
      username: "ops-eu",
      password: "ops-eu-secret",
      source: "paid_provider",
      country: "CA",
      asn: "AS852",
      anonymity: "elite",
      latency_ms: 770,
      success_count: 14,
      fail_count: 1,
      score: 90,
      last_checked_at: hoursAgo(3),
      last_success_at: hoursAgo(3),
      last_error: null,
      status: "elite"
    }),
    createMockProxy({
      scheme: "socks5",
      host: "203.12.19.88",
      port: 1080,
      source: "clash_subscription",
      country: "AU",
      asn: "AS1221",
      anonymity: "anonymous",
      latency_ms: 1010,
      success_count: 9,
      fail_count: 2,
      score: 71,
      last_checked_at: hoursAgo(9),
      last_success_at: hoursAgo(9),
      last_error: null,
      status: "checked"
    }),
    createMockProxy({
      scheme: "http",
      host: "10.0.10.8",
      port: 8899,
      source: "self_hosted",
      country: "US",
      asn: "AS7018",
      anonymity: "elite",
      latency_ms: 430,
      success_count: 63,
      fail_count: 4,
      score: 99,
      last_checked_at: hoursAgo(1),
      last_success_at: hoursAgo(1),
      last_error: null,
      status: "elite"
    }),
    createMockProxy({
      scheme: "socks5",
      host: "121.56.22.9",
      port: 2080,
      source: "freeproxy_provider",
      country: "BR",
      asn: "AS28573",
      anonymity: "unknown",
      latency_ms: null,
      success_count: 1,
      fail_count: 8,
      score: 32,
      last_checked_at: hoursAgo(11),
      last_success_at: hoursAgo(26),
      last_error: "Connection refused",
      status: "dead"
    }),
    createMockProxy({
      scheme: "https",
      host: "45.77.18.61",
      port: 443,
      source: "core_adapter:mihomo",
      country: "US",
      asn: "AS20473",
      anonymity: "elite",
      latency_ms: 560,
      success_count: 18,
      fail_count: 1,
      score: 92,
      last_checked_at: hoursAgo(2),
      last_success_at: hoursAgo(2),
      last_error: null,
      status: "checked"
    }),
    createMockProxy({
      scheme: "http",
      host: "154.18.90.22",
      port: 8088,
      source: "url_list_provider",
      country: "ZA",
      asn: "AS3741",
      anonymity: "transparent",
      latency_ms: 2790,
      success_count: 3,
      fail_count: 9,
      score: 24,
      last_checked_at: hoursAgo(6),
      last_success_at: hoursAgo(16),
      last_error: "Proxy added Via header",
      status: "dead"
    })
  ];
}

let mockProxyStore = buildMockProxyStore();
let mockSettings: DashboardSettings = {
  fetch_interval_seconds: 1800,
  validate_interval_seconds: 600,
  validate_timeout_seconds: 10,
  validate_concurrency: 100,
  min_elite_score: 80,
  cooldown_seconds: 1800,
  safe_networking: {
    authorized_targets_only: true,
    block_private_networks: true,
    mask_proxy_credentials: true
  }
};

const mockValidationJobs: ValidationJob[] = [
  {
    id: "job-2026-05-01-001",
    started_at: hoursAgo(2),
    finished_at: hoursAgo(2),
    checked_count: 420,
    success_count: 133,
    fail_count: 287,
    timeout_count: 41,
    status: "finished"
  },
  {
    id: "job-2026-05-01-002",
    started_at: hoursAgo(6),
    finished_at: hoursAgo(6),
    checked_count: 390,
    success_count: 121,
    fail_count: 269,
    timeout_count: 36,
    status: "finished"
  },
  {
    id: "job-2026-05-01-003",
    started_at: hoursAgo(12),
    finished_at: hoursAgo(12),
    checked_count: 405,
    success_count: 128,
    fail_count: 277,
    timeout_count: 44,
    status: "finished"
  }
];

const mockEvents: EventLogEntry[] = [
  {
    id: "event-001",
    type: "validation_timeout",
    level: "warning",
    message: "Proxy timed out during validation.",
    created_at: hoursAgo(1)
  },
  {
    id: "event-002",
    type: "provider_fetch_error",
    level: "error",
    message: "url_list_provider returned a temporary upstream error.",
    created_at: hoursAgo(3)
  },
  {
    id: "event-003",
    type: "proxy_deleted",
    level: "info",
    message: "Dead proxy removed from the pool after operator review.",
    created_at: hoursAgo(5)
  },
  {
    id: "event-004",
    type: "validation_failed",
    level: "warning",
    message: "Transparent proxy leaked forwarding headers.",
    created_at: hoursAgo(7)
  }
];

export function getMockOverviewData(delayMs = 120): Promise<OverviewData> {
  const payload: OverviewData = {
    stats: {
      ...mockStats,
      last_fetch_at: now(),
      last_validate_at: now()
    },
    health: mockHealth
  };

  if (delayMs <= 0) {
    return Promise.resolve(payload);
  }

  return new Promise((resolve) => {
    globalThis.setTimeout(() => resolve(payload), delayMs);
  });
}

function getProxyFilterOptions(): ProxyFilterOptions {
  return collectProxyFilterOptions(mockProxyStore);
}

function delay<T>(value: T, delayMs: number) {
  if (delayMs <= 0) {
    return Promise.resolve(value);
  }

  return new Promise<T>((resolve) => {
    globalThis.setTimeout(() => resolve(value), delayMs);
  });
}

function paginateItems<T>(items: T[], limit: number, offset: number): PaginatedResponse<T> {
  return {
    items: items.slice(offset, offset + limit),
    total: items.length,
    limit,
    offset
  };
}

export async function listMockProxies(
  query: ProxyListQuery = {},
  delayMs = 120
): Promise<ProxyListResponse> {
  const limit = query.limit ?? 8;
  const offset = query.offset ?? 0;
  const filtered = filterAndSortProxies(mockProxyStore, query);
  const items = filtered.slice(offset, offset + limit).map(cloneProxy);

  return delay(
    {
      items,
      total: filtered.length,
      limit,
      offset
    },
    delayMs
  );
}

export async function getMockProxy(proxyId: string, delayMs = 80): Promise<ProxyEndpoint> {
  const proxy = mockProxyStore.find((item) => item.id === proxyId);
  if (!proxy) {
    throw new Error(`Proxy not found: ${proxyId}`);
  }

  return delay(cloneProxy(proxy), delayMs);
}

export async function deleteMockProxy(
  proxyId: string,
  delayMs = 120
): Promise<DeleteProxyResult> {
  const before = mockProxyStore.length;
  mockProxyStore = mockProxyStore.filter((proxy) => proxy.id !== proxyId);

  return delay(
    {
      ok: mockProxyStore.length < before
    },
    delayMs
  );
}

export async function getMockProxyFilterOptions(delayMs = 40): Promise<ProxyFilterOptions> {
  return delay(getProxyFilterOptions(), delayMs);
}

export async function getMockGeoSummary(delayMs = 80): Promise<GeoSummary> {
  return delay(deriveGeoSummary(mockProxyStore), delayMs);
}

export async function getMockProviders(delayMs = 80): Promise<ProviderSummary[]> {
  return delay(deriveProviderSummaries(mockProxyStore), delayMs);
}

export async function submitMockProxyUrl(
  url: string,
  fileType: ProxyUrlImportFileType,
  delayMs = 120
): Promise<ProxyUrlImportResult> {
  const host = new URL(url).hostname || "mock.local";
  const source = `url_submit:${fileType}:${host}`;
  const directImported = [
    createMockProxy({
      scheme: fileType === "socks5" ? "socks5" : "http",
      host: "11.22.33.44",
      port: fileType === "socks5" ? 1080 : 8080,
      source,
      country: "US",
      asn: "AS64500",
      anonymity: "unknown",
      latency_ms: null,
      success_count: 0,
      fail_count: 0,
      score: 0,
      last_checked_at: null,
      last_success_at: null,
      last_error: null,
      status: "raw"
    }),
    createMockProxy({
      scheme: "https",
      host: "55.66.77.88",
      port: 8443,
      source,
      country: "SG",
      asn: "AS15169",
      anonymity: "unknown",
      latency_ms: null,
      success_count: 0,
      fail_count: 0,
      score: 0,
      last_checked_at: null,
      last_success_at: null,
      last_error: null,
      status: "raw"
    })
  ];
  const adapterRequiredCount = fileType === "v2ray" ? 3 : fileType === "clash" ? 2 : fileType === "auto" ? 1 : 0;
  const unsupportedCount = fileType === "clash" ? 1 : 0;
  const imported = fileType === "v2ray" ? [] : directImported;

  const existingIds = new Set(mockProxyStore.map((proxy) => proxy.id));
  const uniqueImported = imported.filter((proxy) => !existingIds.has(proxy.id));
  mockProxyStore = [...uniqueImported.map(cloneProxy), ...mockProxyStore];

  const detectedFormat =
    fileType === "clash" ? "clash_yaml" : fileType === "v2ray" ? "base64_uri_list" : "plain_text";
  const detectedProtocols =
    fileType === "v2ray"
      ? ["trojan", "vless", "vmess"]
      : fileType === "clash"
        ? ["http", "socks5", "trojan", "vmess"]
        : fileType === "socks5"
          ? ["socks5"]
          : ["http", "https"];

  return delay(
    {
      source,
      file_type: fileType,
      detected_format: detectedFormat,
      fetched_count: directImported.length + adapterRequiredCount + unsupportedCount,
      valid_count: imported.length + adapterRequiredCount,
      stored_count: uniqueImported.length,
      duplicate_count: imported.length - uniqueImported.length,
      invalid_count: 0,
      direct_supported_count: imported.length,
      adapter_required_count: adapterRequiredCount,
      unsupported_count: unsupportedCount,
      detected_protocols: detectedProtocols,
      supported_connection_modes: [
        ...(imported.length > 0 ? ["direct" as const] : []),
        ...(adapterRequiredCount > 0 ? ["core_adapter" as const] : [])
      ]
    },
    delayMs
  );
}

export async function getMockValidationJobs(
  limit = 10,
  offset = 0,
  delayMs = 80
): Promise<PaginatedResponse<ValidationJob>> {
  return delay(
    paginateItems(
      mockValidationJobs.map((item) => ({ ...item })),
      limit,
      offset
    ),
    delayMs
  );
}

export async function getMockEvents(
  limit = 20,
  offset = 0,
  delayMs = 80
): Promise<PaginatedResponse<EventLogEntry>> {
  return delay(
    paginateItems(
      mockEvents.map((item) => ({ ...item })),
      limit,
      offset
    ),
    delayMs
  );
}

export async function getMockSettings(delayMs = 80): Promise<DashboardSettings> {
  return delay(
    {
      ...mockSettings,
      safe_networking: { ...mockSettings.safe_networking }
    },
    delayMs
  );
}

export async function getMockAuthSession(delayMs = 80): Promise<AuthSessionStatus> {
  return delay({ ...mockAuthSession }, delayMs);
}

export async function loginMockDashboard(
  username: string,
  _password: string,
  delayMs = 120
): Promise<AuthSessionStatus> {
  return delay(
    {
      enabled: false,
      authenticated: true,
      username,
      expires_at: null,
      auth_method: "disabled"
    },
    delayMs
  );
}

export async function logoutMockDashboard(delayMs = 80): Promise<AuthSessionStatus> {
  return delay({ ...mockAuthSession }, delayMs);
}

export async function updateMockSettings(
  next: DashboardSettings,
  delayMs = 80
): Promise<DashboardSettings> {
  mockSettings = {
    ...next,
    safe_networking: { ...next.safe_networking }
  };

  return getMockSettings(delayMs);
}

export function resetMockProxyStore() {
  mockProxyStore = buildMockProxyStore();
}
