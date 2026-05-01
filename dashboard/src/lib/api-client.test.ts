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
    expect(overview.stats.redis_status).toBe("ok");
    expect(overview.health.scheduler).toBe("running");
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

  it("maps live overview responses into dashboard overview data", async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            status: "ok",
            app: "ProxyPool Architect",
            version: "0.1.0",
            environment: "dev",
            redis_configured: true
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
    expect(overview.stats.redis_status).toBe("ok");
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

    expect(summary.countries[0].country).toBe("SG");
    expect(summary.countries[0].elite).toBe(1);
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

    const jobs = await client.listValidationJobs();

    expect(jobs.length).toBeGreaterThan(0);
    expect(jobs[0].checked_count).toBeGreaterThan(0);
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
});
