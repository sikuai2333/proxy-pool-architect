import {
  getMockAuthSession,
  getMockSettings,
  deleteMockProxy,
  getMockEvents,
  getMockGeoSummary,
  getMockOverviewData,
  getMockProviders,
  getMockProxy,
  getMockProxyFilterOptions,
  submitMockProxyUrl,
  updateMockSettings,
  getMockValidationJobs,
  loginMockDashboard,
  logoutMockDashboard,
  listMockProxies
} from "./mock-data";
import { collectProxyFilterOptions } from "./proxy-list";
import type {
  AuthSessionStatus,
  DeleteProxyResult,
  DashboardSettings,
  EventLogEntry,
  GeoSummary,
  OverviewData,
  PaginatedResponse,
  ProviderSummary,
  ProxyAnonymity,
  ProxyEndpoint,
  ProxyFilterOptions,
  ProxyUrlImportFileType,
  ProxyUrlImportResult,
  ProxyListQuery,
  ProxyListResponse,
  ValidationJob
} from "../types";
import type { ProxyPool, ProxyScheme } from "../types";
import { deriveGeoSummary, deriveProviderSummaries } from "./dashboard-derive";

export type DashboardDataMode = "mock" | "live";
const LIVE_PROXY_SNAPSHOT_LIMIT = 500;

export interface DashboardApiClientOptions {
  baseUrl?: string;
  mode?: DashboardDataMode;
  mockDelayMs?: number;
  timeoutMs?: number;
}

export interface DashboardApiClient {
  getAuthSession(): Promise<AuthSessionStatus>;
  login(username: string, password: string): Promise<AuthSessionStatus>;
  logout(): Promise<AuthSessionStatus>;
  getOverview(): Promise<OverviewData>;
  listProxies(query: ProxyListQuery): Promise<ProxyListResponse>;
  getProxy(proxyId: string): Promise<ProxyEndpoint>;
  deleteProxy(proxyId: string): Promise<DeleteProxyResult>;
  importProxyUrl(url: string, fileType: ProxyUrlImportFileType): Promise<ProxyUrlImportResult>;
  getProxyFilterOptions(): Promise<ProxyFilterOptions>;
  getGeoSummary(): Promise<GeoSummary>;
  listProviders(): Promise<ProviderSummary[]>;
  listValidationJobs(limit?: number, offset?: number): Promise<PaginatedResponse<ValidationJob>>;
  listEvents(limit?: number, offset?: number): Promise<PaginatedResponse<EventLogEntry>>;
  getSettings(): Promise<DashboardSettings>;
  updateSettings(settings: DashboardSettings): Promise<DashboardSettings>;
}

export class DashboardApiError extends Error {
  status?: number;

  constructor(message: string, status?: number) {
    super(message);
    this.name = "DashboardApiError";
    this.status = status;
  }
}

function getDefaultMode(): DashboardDataMode {
  return import.meta.env.VITE_DASHBOARD_DATA_MODE === "live" ? "live" : "mock";
}

function getDefaultTimeoutMs() {
  const raw = Number(import.meta.env.VITE_API_REQUEST_TIMEOUT_MS ?? 4000);
  return Number.isFinite(raw) && raw > 0 ? raw : 4000;
}

interface LiveHealthResponse {
  status: "ok";
  app: string;
  version: string;
  environment: string;
  db_configured: boolean;
  db?: "ok" | "error" | "unknown";
  scheduler?: "running" | "stopped" | "unknown";
}

interface LiveAuthStatusResponse extends AuthSessionStatus {}

interface LiveStatsResponse {
  pools?: Partial<Record<ProxyPool, number>>;
  total: number;
  average_latency_ms: number | null;
  success_rate: number | null;
  raw?: number;
  checked?: number;
  elite?: number;
  dead?: number;
  cooldown?: number;
  last_fetch_at?: string | null;
  last_validate_at?: string | null;
  db_status?: "ok" | "error" | "unknown";
  scheduler_status?: "running" | "stopped" | "unknown";
}

interface LiveProxyResponse {
  id: string;
  scheme: ProxyScheme;
  host: string;
  port: number;
  auth_required: boolean;
  source: string;
  country?: string | null;
  asn?: string | null;
  anonymity: ProxyAnonymity;
  latency_ms?: number | null;
  success_count: number;
  fail_count: number;
  consecutive_fail_count: number;
  score: number;
  last_checked_at?: string | null;
  last_success_at?: string | null;
  last_error?: string | null;
  cooldown_until?: string | null;
  status: ProxyPool;
}

interface LiveProxyListResponse {
  items?: LiveProxyResponse[];
  total?: number;
  proxies?: LiveProxyResponse[];
  count?: number;
  limit: number;
  offset: number;
}

interface LiveDeleteProxyResponse {
  proxy_id: string;
  deleted: boolean;
}

interface LiveProxyUrlImportResponse extends ProxyUrlImportResult {}

interface LiveGeoSummaryResponse {
  coverage?: GeoSummary["coverage"] | null;
  countries?: GeoSummary["countries"] | null;
  asns?: GeoSummary["asns"] | null;
}

interface LiveProvidersResponse {
  items: ProviderSummary[];
}

interface LiveValidationJobsResponse {
  items: ValidationJob[];
  total: number;
  limit: number;
  offset: number;
}

interface LiveEventsResponse {
  items: EventLogEntry[];
  total: number;
  limit: number;
  offset: number;
}

interface LiveSettingsResponse extends DashboardSettings {}

function normalizeLiveProxy(proxy: LiveProxyResponse): ProxyEndpoint {
  return {
    id: proxy.id,
    scheme: proxy.scheme,
    host: proxy.host,
    port: proxy.port,
    auth_required: proxy.auth_required,
    username: null,
    password: null,
    source: proxy.source,
    country: proxy.country ?? null,
    asn: proxy.asn ?? null,
    anonymity: proxy.anonymity,
    latency_ms: proxy.latency_ms ?? null,
    success_count: proxy.success_count,
    fail_count: proxy.fail_count,
    consecutive_fail_count: proxy.consecutive_fail_count,
    score: proxy.score,
    last_checked_at: proxy.last_checked_at ?? null,
    last_success_at: proxy.last_success_at ?? null,
    last_error: proxy.last_error ?? null,
    cooldown_until: proxy.cooldown_until ?? null,
    status: proxy.status
  };
}

function normalizeGeoSummary(payload: LiveGeoSummaryResponse): GeoSummary {
  const countries = payload.countries ?? [];
  const asns = payload.asns ?? [];
  const inferredTotal = Math.max(
    countries.reduce((sum, item) => sum + item.total, 0),
    asns.reduce((sum, item) => sum + item.total, 0)
  );
  const coverage = payload.coverage ?? {
    total_proxies: inferredTotal,
    geo_tagged_proxies: inferredTotal,
    unresolved_proxies: 0,
    geo_enabled: inferredTotal > 0,
    geo_file: "",
    geo_file_exists: inferredTotal > 0
  };

  return {
    coverage,
    countries,
    asns
  };
}

export function createDashboardApiClient(
  options: DashboardApiClientOptions = {}
): DashboardApiClient {
  const mode = options.mode ?? getDefaultMode();
  const mockDelayMs = options.mockDelayMs ?? 120;
  const baseUrl = options.baseUrl ?? import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";
  const timeoutMs = options.timeoutMs ?? getDefaultTimeoutMs();
  const proxyCache = new Map<string, ProxyEndpoint>();

  function cacheProxies(items: ProxyEndpoint[]) {
    items.forEach((item) => {
      proxyCache.set(item.id, item);
    });
  }

  async function parseError(response: Response) {
    const contentType = response.headers.get("content-type") ?? "";
    if (contentType.includes("application/json")) {
      const payload = (await response.json()) as { detail?: string };
      if (payload.detail) {
        return payload.detail;
      }
    }

    const text = await response.text();
    return text || `Request failed with status ${response.status}`;
  }

  async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
    const controller = new AbortController();
    let timer: ReturnType<typeof globalThis.setTimeout> | undefined;
    const timeoutPromise = new Promise<never>((_, reject) => {
      timer = globalThis.setTimeout(() => {
        controller.abort();
        reject(new DashboardApiError(`Request timed out after ${timeoutMs}ms`));
      }, timeoutMs);
    });

    try {
      const response = await Promise.race([
        fetch(`${baseUrl}${path}`, {
          ...init,
          headers: {
            Accept: "application/json",
            ...(init?.headers ?? {})
          },
          credentials: "include",
          signal: controller.signal
        }),
        timeoutPromise
      ]);

      if (!response.ok) {
        const detail = await parseError(response);
        throw new DashboardApiError(detail, response.status);
      }

      return (await response.json()) as T;
    } catch (error) {
      if (error instanceof DashboardApiError) {
        throw error;
      }

      if (error instanceof DOMException && error.name === "AbortError") {
        throw new DashboardApiError(`Request timed out after ${timeoutMs}ms`);
      }

      throw new DashboardApiError(
        error instanceof Error ? error.message : "Unexpected API request failure"
      );
    } finally {
      if (timer) {
        globalThis.clearTimeout(timer);
      }
    }
  }

  function buildPaginationPath(path: string, limit: number, offset: number) {
    const params = new URLSearchParams();
    params.set("limit", String(limit));
    params.set("offset", String(offset));
    return `${path}?${params.toString()}`;
  }

  function buildLiveProxyListPath(query: ProxyListQuery) {
    const params = new URLSearchParams();
    params.set("limit", String(query.limit ?? LIVE_PROXY_SNAPSHOT_LIMIT));
    params.set("offset", String(query.offset ?? 0));

    if (query.pool) {
      params.set("pool", query.pool);
    }

    if (query.scheme) {
      params.set("scheme", query.scheme);
    }
    if (query.anonymity) {
      params.set("anonymity", query.anonymity);
    }
    if (query.country) {
      params.set("country", query.country);
    }
    if (query.source) {
      params.set("source", query.source);
    }
    if (query.q) {
      params.set("q", query.q);
    }
    if (query.min_score != null) {
      params.set("min_score", String(query.min_score));
    }

    return `/proxy/list?${params.toString()}`;
  }

  async function loadLiveProxyUniverse(query: ProxyListQuery) {
    const response = await fetchJson<LiveProxyListResponse>(
      buildLiveProxyListPath({ ...query, limit: LIVE_PROXY_SNAPSHOT_LIMIT, offset: 0 })
    );
    const rawItems = response.items ?? response.proxies ?? [];
    const items = rawItems.map(normalizeLiveProxy);
    cacheProxies(items);
    return items;
  }

  return {
    async getAuthSession() {
      if (mode === "mock") {
        return getMockAuthSession(mockDelayMs);
      }

      return fetchJson<LiveAuthStatusResponse>("/auth/session");
    },

    async login(username, password) {
      if (mode === "mock") {
        return loginMockDashboard(username, password, mockDelayMs);
      }

      return fetchJson<LiveAuthStatusResponse>("/auth/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ username, password })
      });
    },

    async logout() {
      if (mode === "mock") {
        return logoutMockDashboard(mockDelayMs);
      }

      return fetchJson<LiveAuthStatusResponse>("/auth/logout", {
        method: "POST"
      });
    },

    async getOverview() {
      if (mode === "mock") {
        return getMockOverviewData(mockDelayMs);
      }

      const [health, stats] = await Promise.all([
        fetchJson<LiveHealthResponse>("/health"),
        fetchJson<LiveStatsResponse>("/stats")
      ]);

      return {
        stats: {
          raw: stats.raw ?? stats.pools?.raw ?? 0,
          checked: stats.checked ?? stats.pools?.checked ?? 0,
          elite: stats.elite ?? stats.pools?.elite ?? 0,
          dead: stats.dead ?? stats.pools?.dead ?? 0,
          cooldown: stats.cooldown ?? stats.pools?.cooldown ?? 0,
          avg_latency_ms: stats.average_latency_ms,
          success_rate: stats.success_rate,
          last_fetch_at: stats.last_fetch_at ?? null,
          last_validate_at: stats.last_validate_at ?? null,
          db_status: stats.db_status ?? health.db ?? (health.db_configured ? "ok" : "unknown"),
          scheduler_status: stats.scheduler_status ?? health.scheduler ?? "unknown"
        },
        health: {
          status: health.status,
          db: health.db ?? (health.db_configured ? "ok" : "unknown"),
          scheduler: health.scheduler ?? "unknown"
        }
      };
    },

    async listProxies(query) {
      if (mode === "mock") {
        return listMockProxies(query, mockDelayMs);
      }

      const response = await fetchJson<LiveProxyListResponse>(buildLiveProxyListPath(query));
      const items = (response.items ?? response.proxies ?? []).map(normalizeLiveProxy);
      cacheProxies(items);

      return {
        items,
        total: response.total ?? response.count ?? items.length,
        limit: response.limit,
        offset: response.offset
      };
    },

    async getProxy(proxyId) {
      if (mode === "mock") {
        return getMockProxy(proxyId, mockDelayMs);
      }

      try {
        const response = await fetchJson<LiveProxyResponse>(`/proxy/${encodeURIComponent(proxyId)}`);
        const normalized = normalizeLiveProxy(response);
        proxyCache.set(normalized.id, normalized);
        return normalized;
      } catch (error) {
        const cached = proxyCache.get(proxyId);
        if (cached) {
          return cached;
        }

        if (error instanceof DashboardApiError && error.status === 404) {
          throw new DashboardApiError(`Proxy ${proxyId} was not found.`, 404);
        }

        throw error;
      }
    },

    async deleteProxy(proxyId) {
      if (mode === "mock") {
        return deleteMockProxy(proxyId, mockDelayMs);
      }

      const response = await fetchJson<LiveDeleteProxyResponse>(`/proxy/${encodeURIComponent(proxyId)}`, {
        method: "DELETE"
      });
      proxyCache.delete(proxyId);
      return { ok: response.deleted };
    },

    async importProxyUrl(url, fileType) {
      if (mode === "mock") {
        return submitMockProxyUrl(url, fileType, mockDelayMs);
      }

      return fetchJson<LiveProxyUrlImportResponse>("/providers/import-url", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          url,
          file_type: fileType
        })
      });
    },

    async getProxyFilterOptions() {
      if (mode === "mock") {
        return getMockProxyFilterOptions(mockDelayMs);
      }

      const universe = await loadLiveProxyUniverse({ limit: LIVE_PROXY_SNAPSHOT_LIMIT, offset: 0 });
      return collectProxyFilterOptions(universe);
    },

    async getGeoSummary() {
      if (mode === "mock") {
        return getMockGeoSummary(mockDelayMs);
      }

      try {
        const response = await fetchJson<LiveGeoSummaryResponse>("/geo/summary");
        return normalizeGeoSummary(response);
      } catch (error) {
        if (!(error instanceof DashboardApiError) || error.status !== 404) {
          throw error;
        }

        const universe = await loadLiveProxyUniverse({ limit: LIVE_PROXY_SNAPSHOT_LIMIT, offset: 0 });
        return deriveGeoSummary(universe);
      }
    },

    async listProviders() {
      if (mode === "mock") {
        return getMockProviders(mockDelayMs);
      }

      try {
        const response = await fetchJson<LiveProvidersResponse>("/providers");
        return response.items;
      } catch (error) {
        if (!(error instanceof DashboardApiError) || error.status !== 404) {
          throw error;
        }

        const universe = await loadLiveProxyUniverse({ limit: LIVE_PROXY_SNAPSHOT_LIMIT, offset: 0 });
        return deriveProviderSummaries(universe);
      }
    },

    async listValidationJobs(limit = 10, offset = 0) {
      if (mode === "mock") {
        return getMockValidationJobs(limit, offset, mockDelayMs);
      }

      try {
        return await fetchJson<LiveValidationJobsResponse>(
          buildPaginationPath("/validation/jobs", limit, offset)
        );
      } catch (error) {
        if (!(error instanceof DashboardApiError) || error.status !== 404) {
          throw error;
        }

        return getMockValidationJobs(limit, offset, mockDelayMs);
      }
    },

    async listEvents(limit = 20, offset = 0) {
      if (mode === "mock") {
        return getMockEvents(limit, offset, mockDelayMs);
      }

      try {
        return await fetchJson<LiveEventsResponse>(buildPaginationPath("/events", limit, offset));
      } catch (error) {
        if (!(error instanceof DashboardApiError) || error.status !== 404) {
          throw error;
        }

        return getMockEvents(limit, offset, mockDelayMs);
      }
    },

    async getSettings() {
      if (mode === "mock") {
        return getMockSettings(mockDelayMs);
      }

      try {
        return await fetchJson<LiveSettingsResponse>("/settings");
      } catch (error) {
        if (!(error instanceof DashboardApiError) || error.status !== 404) {
          throw error;
        }

        return getMockSettings(mockDelayMs);
      }
    },

    async updateSettings(settings) {
      if (mode === "mock") {
        return updateMockSettings(settings, mockDelayMs);
      }

      try {
        return await fetchJson<LiveSettingsResponse>("/settings", {
          method: "PATCH",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify(settings)
        });
      } catch (error) {
        if (!(error instanceof DashboardApiError) || error.status !== 404) {
          throw error;
        }

        return updateMockSettings(settings, mockDelayMs);
      }
    }
  };
}

export const dashboardApi = createDashboardApiClient();
export const dashboardDataMode = getDefaultMode();
