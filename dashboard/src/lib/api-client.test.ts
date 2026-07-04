import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { DashboardApiError, createDashboardApiClient } from "./api-client";
import { resetMockProxyStore } from "./mock-data";

describe("dashboard API client", () => {
  beforeEach(() => {
    resetMockProxyStore();
    vi.restoreAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("returns overview mock data", async () => {
    const client = createDashboardApiClient({ mode: "mock", mockDelayMs: 0 });

    const overview = await client.getOverview();

    expect(overview.stats.raw).toBeGreaterThan(0);
    expect(overview.stats.db_status).toBe("ok");
    expect(overview.health.scheduler).toBe("running");
  });

  it("returns mock auth state and supports mock login/logout", async () => {
    const client = createDashboardApiClient({ mode: "mock", mockDelayMs: 0 });

    const initial = await client.getAuthSession();
    expect(initial.enabled).toBe(false);
    expect(initial.authenticated).toBe(false);

    const loggedIn = await client.login("admin", "test-password-2333");
    expect(loggedIn.authenticated).toBe(true);
    expect(loggedIn.username).toBe("admin");

    const loggedOut = await client.logout();
    expect(loggedOut.authenticated).toBe(false);
  });

  it("raises API errors when live overview requests fail", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ detail: "Service unavailable" }), {
        status: 503,
        headers: { "Content-Type": "application/json" }
      })
    );
    vi.stubGlobal("fetch", fetchMock);

    const client = createDashboardApiClient({
      mode: "live",
      baseUrl: "http://dashboard.test",
      timeoutMs: 1000,
      mockDelayMs: 0
    });

    await expect(client.getOverview()).rejects.toBeInstanceOf(DashboardApiError);
  });

  it("filters and paginates mock proxies", async () => {
    const client = createDashboardApiClient({ mode: "mock", mockDelayMs: 0 });

    const page = await client.listProxies({
      pool: "elite",
      scheme: "https",
      min_score: 90,
      limit: 2,
      offset: 0
    });

    expect(page.items).toHaveLength(2);
    expect(page.total).toBeGreaterThanOrEqual(2);
    expect(page.items.every((item) => item.status === "elite")).toBe(true);
    expect(page.items.every((item) => item.scheme === "https")).toBe(true);
  });

  it("returns proxy detail from the mock store", async () => {
    const client = createDashboardApiClient({ mode: "mock", mockDelayMs: 0 });
    const page = await client.listProxies({ limit: 1, offset: 0 });

    const proxy = await client.getProxy(page.items[0].id);

    expect(proxy.id).toBe(page.items[0].id);
    expect(proxy.host).toBeTruthy();
  });

  it("deletes a proxy from the mock store", async () => {
    const client = createDashboardApiClient({ mode: "mock", mockDelayMs: 0 });
    const page = await client.listProxies({ limit: 50, offset: 0 });
    const target = page.items[0];

    const result = await client.deleteProxy(target.id);
    const afterDelete = await client.listProxies({ limit: 50, offset: 0 });

    expect(result.ok).toBe(true);
    expect(afterDelete.items.find((item) => item.id === target.id)).toBeUndefined();
    expect(afterDelete.total).toBe(page.total - 1);
  });

  it("imports proxy URLs in mock mode and exposes the imported source", async () => {
    const client = createDashboardApiClient({ mode: "mock", mockDelayMs: 0 });

    const result = await client.importProxyUrl("https://example.com/http.txt", "http");
    const providers = await client.listProviders();

    expect(result.source).toBe("url_submit:http:example.com");
    expect(result.detected_format).toBe("plain_text");
    expect(result.stored_count).toBeGreaterThan(0);
    expect(providers.some((provider) => provider.name === result.source)).toBe(true);
  });

  it("maps live overview responses into dashboard overview data", async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            status: "ok",
            app: "ProxyPool Architect",
            version: "0.1.0",
            environment: "dev",
            db_configured: true
          }),
          { status: 200, headers: { "Content-Type": "application/json" } }
        )
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            pools: { raw: 4, checked: 2, elite: 1, dead: 3, cooldown: 1 },
            total: 11,
            average_latency_ms: 820,
            success_rate: 0.75
          }),
          { status: 200, headers: { "Content-Type": "application/json" } }
        )
      );
    vi.stubGlobal("fetch", fetchMock);

    const client = createDashboardApiClient({
      mode: "live",
      baseUrl: "http://localhost:8000",
      timeoutMs: 1000
    });

    const overview = await client.getOverview();

    expect(overview.stats.elite).toBe(1);
    expect(overview.stats.db_status).toBe("ok");
    expect(overview.health.scheduler).toBe("unknown");
  });

  it("maps live proxy list responses and applies client-side filters", async () => {
    const fetchMock = vi.fn().mockImplementation(
      async () =>
        new Response(
          JSON.stringify({
            proxies: [
              {
                id: "https-34.76.12.10-8443",
                scheme: "https",
                host: "34.76.12.10",
                port: 8443,
                auth_required: false,
                source: "static_provider",
                country: "SG",
                asn: "AS15169",
                anonymity: "elite",
                latency_ms: 640,
                success_count: 28,
                fail_count: 0,
                consecutive_fail_count: 0,
                score: 95,
                last_checked_at: "2026-05-01T00:00:00+08:00",
                last_success_at: "2026-05-01T00:00:00+08:00",
                last_error: null,
                cooldown_until: null,
                status: "elite"
              }
            ],
            count: 1,
            limit: 500,
            offset: 0
          }),
          { status: 200, headers: { "Content-Type": "application/json" } }
        )
    );
    vi.stubGlobal("fetch", fetchMock);

    const client = createDashboardApiClient({
      mode: "live",
      baseUrl: "http://localhost:8000",
      timeoutMs: 1000
    });

    const list = await client.listProxies({
      pool: "elite",
      source: "static_provider",
      limit: 8,
      offset: 0
    });

    expect(list.total).toBe(1);
    expect(list.items[0].auth_required).toBe(false);
    expect(list.items[0].source).toBe("static_provider");
  });

  it("falls back to cached proxy data when the live detail endpoint is missing", async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            proxies: [
              {
                id: "socks5-1.2.3.4-1080",
                scheme: "socks5",
                host: "1.2.3.4",
                port: 1080,
                auth_required: true,
                source: "core_adapter:mihomo",
                country: "US",
                asn: "AS12345",
                anonymity: "elite",
                latency_ms: 820,
                success_count: 12,
                fail_count: 1,
                consecutive_fail_count: 0,
                score: 91,
                last_checked_at: "2026-05-01T00:00:00+08:00",
                last_success_at: "2026-05-01T00:00:00+08:00",
                last_error: null,
                cooldown_until: null,
                status: "elite"
              }
            ],
            count: 1,
            limit: 500,
            offset: 0
          }),
          { status: 200, headers: { "Content-Type": "application/json" } }
        )
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ detail: "Not Found" }), {
          status: 404,
          headers: { "Content-Type": "application/json" }
        })
      );
    vi.stubGlobal("fetch", fetchMock);

    const client = createDashboardApiClient({
      mode: "live",
      baseUrl: "http://localhost:8000",
      timeoutMs: 1000
    });

    const list = await client.listProxies({ pool: "elite", limit: 8, offset: 0 });
    const proxy = await client.getProxy(list.items[0].id);

    expect(proxy.id).toBe(list.items[0].id);
    expect(proxy.source).toBe("core_adapter:mihomo");
  });

  it("posts submitted proxy URLs to the live import endpoint", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          source: "url_submit:http:example.com",
          file_type: "http",
          detected_format: "plain_text",
          fetched_count: 2,
          valid_count: 2,
          stored_count: 1,
          duplicate_count: 1,
          invalid_count: 0,
          direct_supported_count: 2,
          adapter_required_count: 0,
          unsupported_count: 0,
          detected_protocols: ["http"],
          supported_connection_modes: ["direct"]
        }),
        { status: 200, headers: { "Content-Type": "application/json" } }
      )
    );
    vi.stubGlobal("fetch", fetchMock);

    const client = createDashboardApiClient({
      mode: "live",
      baseUrl: "http://localhost:8000",
      timeoutMs: 1000
    });

    const result = await client.importProxyUrl("https://example.com/http.txt", "http");

    expect(result.stored_count).toBe(1);
    expect(result.detected_protocols).toEqual(["http"]);
    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/providers/import-url",
      expect.objectContaining({
        credentials: "include",
        method: "POST",
        body: JSON.stringify({
          url: "https://example.com/http.txt",
          file_type: "http"
        })
      })
    );
  });

  it("calls live auth endpoints with cookie credentials", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            enabled: true,
            authenticated: false,
            username: null,
            expires_at: null,
            auth_method: null
          }),
          { status: 200, headers: { "Content-Type": "application/json" } }
        )
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            enabled: true,
            authenticated: true,
            username: "sikuai",
            expires_at: "2026-05-01T12:00:00+08:00",
            auth_method: "session"
          }),
          { status: 200, headers: { "Content-Type": "application/json" } }
        )
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            enabled: true,
            authenticated: false,
            username: null,
            expires_at: null,
            auth_method: null
          }),
          { status: 200, headers: { "Content-Type": "application/json" } }
        )
      );
    vi.stubGlobal("fetch", fetchMock);

    const client = createDashboardApiClient({
      mode: "live",
      baseUrl: "http://localhost:8000",
      timeoutMs: 1000
    });

    const session = await client.getAuthSession();
    expect(session.authenticated).toBe(false);

    const login = await client.login("admin", "test-password-2333");
    expect(login.authenticated).toBe(true);
    expect(login.username).toBe("admin");

    const logout = await client.logout();
    expect(logout.authenticated).toBe(false);

    expect(fetchMock).toHaveBeenNthCalledWith(
      1,
      "http://localhost:8000/auth/session",
      expect.objectContaining({
        credentials: "include"
      })
    );
    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      "http://localhost:8000/auth/login",
      expect.objectContaining({
        credentials: "include",
        method: "POST",
        body: JSON.stringify({
          username: "admin",
          password: "test-password-2333"
        })
      })
    );
    expect(fetchMock).toHaveBeenNthCalledWith(
      3,
      "http://localhost:8000/auth/logout",
      expect.objectContaining({
        credentials: "include",
        method: "POST"
      })
    );
  });

  it("derives geo summary from live proxy snapshots when /geo/summary is missing", async () => {
    const snapshotPayload = {
      proxies: [
        {
          id: "https-34.76.12.10-8443",
          scheme: "https",
          host: "34.76.12.10",
          port: 8443,
          auth_required: false,
          source: "static_provider",
          country: "SG",
          asn: "AS15169",
          anonymity: "elite",
          latency_ms: 640,
          success_count: 28,
          fail_count: 0,
          consecutive_fail_count: 0,
          score: 95,
          last_checked_at: "2026-05-01T00:00:00+08:00",
          last_success_at: "2026-05-01T00:00:00+08:00",
          last_error: null,
          cooldown_until: null,
          status: "elite"
        }
      ],
      count: 1,
      limit: 500,
      offset: 0
    };
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ detail: "Not Found" }), {
          status: 404,
          headers: { "Content-Type": "application/json" }
        })
      )
      .mockImplementation(async () =>
        new Response(JSON.stringify(snapshotPayload), {
          status: 200,
          headers: { "Content-Type": "application/json" }
        })
      );
    vi.stubGlobal("fetch", fetchMock);

    const client = createDashboardApiClient({
      mode: "live",
      baseUrl: "http://localhost:8000",
      timeoutMs: 1000
    });

    const summary = await client.getGeoSummary();

    expect(summary.coverage.total_proxies).toBe(1);
    expect(summary.coverage.geo_tagged_proxies).toBe(1);
    expect(summary.countries[0].country).toBe("SG");
    expect(summary.countries[0].elite).toBe(1);
  });

  it("maps live geo summary responses with country and ASN latency data", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          coverage: {
            total_proxies: 4,
            geo_tagged_proxies: 4,
            unresolved_proxies: 0,
            geo_enabled: true,
            geo_file: "config/geo.csv",
            geo_file_exists: true
          },
          countries: [{ country: "US", total: 4, elite: 2, avg_latency_ms: 610 }],
          asns: [{ asn: "AS20473", total: 3, elite: 1, avg_latency_ms: 560 }]
        }),
        { status: 200, headers: { "Content-Type": "application/json" } }
      )
    );
    vi.stubGlobal("fetch", fetchMock);

    const client = createDashboardApiClient({
      mode: "live",
      baseUrl: "http://localhost:8000",
      timeoutMs: 1000
    });

    const summary = await client.getGeoSummary();

    expect(summary.coverage.geo_enabled).toBe(true);
    expect(summary.countries[0]).toMatchObject({
      country: "US",
      total: 4,
      elite: 2,
      avg_latency_ms: 610
    });
    expect(summary.asns[0]).toMatchObject({
      asn: "AS20473",
      avg_latency_ms: 560
    });
    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/geo/summary",
      expect.objectContaining({
        headers: expect.objectContaining({ Accept: "application/json" })
      })
    );
  });

  it("normalizes legacy live geo summary responses without coverage", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          countries: [{ country: "JP", total: 2, elite: 1, avg_latency_ms: 720 }],
          asns: []
        }),
        { status: 200, headers: { "Content-Type": "application/json" } }
      )
    );
    vi.stubGlobal("fetch", fetchMock);

    const client = createDashboardApiClient({
      mode: "live",
      baseUrl: "http://localhost:8000",
      timeoutMs: 1000
    });

    const summary = await client.getGeoSummary();

    expect(summary.coverage).toMatchObject({
      total_proxies: 2,
      geo_tagged_proxies: 2,
      unresolved_proxies: 0
    });
    expect(summary.countries[0].country).toBe("JP");
  });

  it("derives provider summaries from live proxy snapshots when /providers is missing", async () => {
    const snapshotPayload = {
      proxies: [
        {
          id: "http-8.8.4.2-8080",
          scheme: "http",
          host: "8.8.4.2",
          port: 8080,
          auth_required: false,
          source: "url_list_provider",
          country: "DE",
          asn: "AS3320",
          anonymity: "anonymous",
          latency_ms: 1130,
          success_count: 16,
          fail_count: 3,
          consecutive_fail_count: 0,
          score: 79,
          last_checked_at: "2026-05-01T00:00:00+08:00",
          last_success_at: "2026-05-01T00:00:00+08:00",
          last_error: null,
          cooldown_until: null,
          status: "checked"
        }
      ],
      count: 1,
      limit: 500,
      offset: 0
    };
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ detail: "Not Found" }), {
          status: 404,
          headers: { "Content-Type": "application/json" }
        })
      )
      .mockImplementation(async () =>
        new Response(JSON.stringify(snapshotPayload), {
          status: 200,
          headers: { "Content-Type": "application/json" }
        })
      );
    vi.stubGlobal("fetch", fetchMock);

    const client = createDashboardApiClient({
      mode: "live",
      baseUrl: "http://localhost:8000",
      timeoutMs: 1000
    });

    const providers = await client.listProviders();

    expect(providers[0].name).toBe("url_list_provider");
    expect(providers[0].valid_count).toBe(1);
  });

  it("falls back to mock validation jobs when the live endpoint is missing", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ detail: "Not Found" }), {
        status: 404,
        headers: { "Content-Type": "application/json" }
      })
    );
    vi.stubGlobal("fetch", fetchMock);

    const client = createDashboardApiClient({
      mode: "live",
      baseUrl: "http://localhost:8000",
      timeoutMs: 1000
    });

    const jobs = await client.listValidationJobs(10, 0);

    expect(jobs.items.length).toBeGreaterThan(0);
    expect(jobs.items[0].checked_count).toBeGreaterThan(0);
  });

  it("maps paginated live validation jobs and events", async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            items: [
              {
                id: "job-001",
                started_at: "2026-05-01T00:00:00+08:00",
                finished_at: "2026-05-01T00:01:00+08:00",
                checked_count: 10,
                success_count: 5,
                fail_count: 5,
                timeout_count: 1,
                status: "finished"
              }
            ],
            total: 3,
            limit: 1,
            offset: 1
          }),
          { status: 200, headers: { "Content-Type": "application/json" } }
        )
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            items: [
              {
                id: "event-001",
                type: "validation_timeout",
                level: "warning",
                message: "timeout",
                created_at: "2026-05-01T00:02:00+08:00"
              }
            ],
            total: 6,
            limit: 1,
            offset: 2
          }),
          { status: 200, headers: { "Content-Type": "application/json" } }
        )
      );
    vi.stubGlobal("fetch", fetchMock);

    const client = createDashboardApiClient({
      mode: "live",
      baseUrl: "http://localhost:8000",
      timeoutMs: 1000
    });

    const jobs = await client.listValidationJobs(1, 1);
    const events = await client.listEvents(1, 2);

    expect(jobs.total).toBe(3);
    expect(jobs.items[0].id).toBe("job-001");
    expect(events.total).toBe(6);
    expect(events.items[0].id).toBe("event-001");
    expect(fetchMock).toHaveBeenNthCalledWith(
      1,
      "http://localhost:8000/validation/jobs?limit=1&offset=1",
      expect.objectContaining({
        headers: expect.objectContaining({ Accept: "application/json" })
      })
    );
    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      "http://localhost:8000/events?limit=1&offset=2",
      expect.objectContaining({
        headers: expect.objectContaining({ Accept: "application/json" })
      })
    );
  });

  it("falls back to mock settings when the live settings endpoint is missing", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ detail: "Not Found" }), {
        status: 404,
        headers: { "Content-Type": "application/json" }
      })
    );
    vi.stubGlobal("fetch", fetchMock);

    const client = createDashboardApiClient({
      mode: "live",
      baseUrl: "http://localhost:8000",
      timeoutMs: 1000
    });

    const settings = await client.getSettings();

    expect(settings.validate_concurrency).toBeGreaterThan(0);
    expect(settings.safe_networking.mask_proxy_credentials).toBe(true);
  });

  it("times out hanging live requests instead of waiting forever", async () => {
    const fetchMock = vi.fn().mockImplementation(() => new Promise(() => undefined));
    vi.stubGlobal("fetch", fetchMock);

    const client = createDashboardApiClient({
      mode: "live",
      baseUrl: "http://localhost:8000",
      timeoutMs: 25
    });

    await expect(client.getOverview()).rejects.toMatchObject({
      name: "DashboardApiError",
      message: "Request timed out after 25ms"
    });
  });
});
