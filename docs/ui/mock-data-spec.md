# Dashboard Mock Data Spec

Use mock mode while backend endpoints are incomplete.

## Mock Stats

```ts
export const mockStats = {
  raw: 1280,
  checked: 342,
  elite: 76,
  dead: 862,
  cooldown: 18,
  avg_latency_ms: 1240,
  success_rate: 0.72,
  last_fetch_at: new Date().toISOString(),
  last_validate_at: new Date().toISOString(),
  redis_status: 'ok',
  scheduler_status: 'running',
};
```

## Mock Proxy Item

```ts
export const mockProxy = {
  id: 'socks5-1.2.3.4-1080',
  scheme: 'socks5',
  host: '1.2.3.4',
  port: 1080,
  username: null,
  source: 'url_list_provider',
  country: 'US',
  asn: 'AS12345',
  anonymity: 'elite',
  latency_ms: 820,
  success_count: 12,
  fail_count: 1,
  score: 91,
  last_checked_at: new Date().toISOString(),
  last_success_at: new Date().toISOString(),
  last_error: null,
  status: 'elite',
};
```

## Mock Mode Rules

1. Mock data must be isolated in `mock-data.ts`.
2. API client should support switching between mock and live mode.
3. UI should behave the same in mock and live modes.
4. Do not hide missing backend endpoints. Add TODOs.
