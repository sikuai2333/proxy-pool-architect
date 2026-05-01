# ProxyPool Architect Web Dashboard Plan

## 1. Goal

Build a web dashboard for ProxyPool Architect to help the user monitor proxy pool status, proxy lists, validation results, geo distribution, provider health, latency, anonymity leakage status, and operational logs.

The dashboard is for authorized proxy quality management and network diagnostics only. It must not include anti-bot bypass, CAPTCHA bypass, stealth automation, account abuse, WAF bypass, or target-specific evasion features.

## 2. Recommended Stack

Preferred frontend stack:

- Next.js 14+ or Vite + React
- TypeScript
- Tailwind CSS
- shadcn/ui
- Recharts for charts
- TanStack Table for proxy lists
- TanStack Query for API state
- Zustand or simple React state for UI filters

If the current backend is FastAPI, the dashboard can be one of two forms:

1. Separate frontend app under `dashboard/`.
2. Static build served by FastAPI later.

Recommended for MVP: separate frontend app under `dashboard/`.

## 3. Dashboard Scope

### MVP Pages

1. Overview
2. Proxy List
3. Proxy Detail Drawer
4. Providers
5. Validation Status
6. Geo / ASN Insights
7. Settings
8. Logs / Events

### Later Pages

1. Rule / Policy Management
2. Alerting
3. Prometheus Metrics View
4. Admin User Management
5. Paid Provider Integration

## 4. Information Architecture

```text
Dashboard
├─ Overview
│  ├─ Total proxies
│  ├─ Raw / Checked / Elite / Dead counts
│  ├─ Success rate
│  ├─ Average latency
│  ├─ Last fetch time
│  ├─ Last validation time
│  └─ System health
│
├─ Proxy List
│  ├─ Filter by pool
│  ├─ Filter by scheme
│  ├─ Filter by anonymity
│  ├─ Filter by country
│  ├─ Filter by provider
│  ├─ Filter by min score
│  ├─ Search host / IP
│  └─ Table actions
│
├─ Geo Insights
│  ├─ Country distribution
│  ├─ ASN distribution
│  ├─ Latency by country
│  └─ Elite proxy distribution
│
├─ Providers
│  ├─ Provider list
│  ├─ Enabled / disabled status
│  ├─ Last fetch result
│  ├─ Fetched count
│  ├─ Valid count
│  └─ Error summary
│
├─ Validation
│  ├─ Recent validation jobs
│  ├─ Success / fail trend
│  ├─ Common error types
│  ├─ Timeout rate
│  └─ Dead proxy count
│
├─ Logs
│  ├─ Fetch events
│  ├─ Validation events
│  ├─ API usage events
│  └─ Error events
│
└─ Settings
   ├─ Validation concurrency
   ├─ Validation timeout
   ├─ Fetch interval
   ├─ Validate interval
   ├─ Minimum elite score
   └─ Safe networking controls
```

## 5. Visual Style

Use a clean infrastructure-dashboard style:

- Dark mode first, light mode optional.
- Dense but readable data tables.
- Card-based overview metrics.
- Subtle gradients, no flashy effects.
- Use badges for status, scheme, anonymity, and pool.
- Prefer charts that answer operational questions.
- Keep actions explicit and safe.

Suggested status colors:

- Elite: green
- Checked: blue
- Raw: gray
- Dead: red
- Cooldown: amber
- Unknown: neutral

Do not hard-code exact colors if the project already has a theme system.

## 6. Core Components

```text
components/
├─ layout/
│  ├─ AppShell.tsx
│  ├─ Sidebar.tsx
│  ├─ Header.tsx
│  └─ PageHeader.tsx
│
├─ dashboard/
│  ├─ MetricCard.tsx
│  ├─ PoolDistributionChart.tsx
│  ├─ SuccessRateChart.tsx
│  ├─ LatencyTrendChart.tsx
│  └─ SystemHealthPanel.tsx
│
├─ proxies/
│  ├─ ProxyTable.tsx
│  ├─ ProxyFilters.tsx
│  ├─ ProxyDetailDrawer.tsx
│  ├─ ProxyStatusBadge.tsx
│  ├─ AnonymityBadge.tsx
│  └─ SchemeBadge.tsx
│
├─ geo/
│  ├─ CountryDistributionChart.tsx
│  ├─ AsnDistributionTable.tsx
│  └─ GeoLatencyChart.tsx
│
├─ providers/
│  ├─ ProviderTable.tsx
│  ├─ ProviderStatusBadge.tsx
│  └─ ProviderDetailPanel.tsx
│
├─ validation/
│  ├─ ValidationJobTable.tsx
│  ├─ ErrorTypeChart.tsx
│  └─ ValidationTrendChart.tsx
│
└─ common/
   ├─ EmptyState.tsx
   ├─ ErrorState.tsx
   ├─ LoadingState.tsx
   └─ ConfirmDialog.tsx
```

## 7. API Contract

The frontend should call backend APIs through a typed client.

Recommended endpoints:

```http
GET /health
GET /stats
GET /proxy/list
GET /proxy/{proxy_id}
DELETE /proxy/{proxy_id}
POST /proxy/report
GET /providers
GET /providers/{provider_name}
GET /validation/jobs
GET /events
GET /geo/summary
GET /settings
PATCH /settings
```

If some endpoints do not exist yet, implement mock data first and create TODOs for backend integration.

## 8. Data Types

### ProxyEndpoint

```ts
export type ProxyPool = 'raw' | 'checked' | 'elite' | 'dead' | 'cooldown';
export type ProxyScheme = 'http' | 'https' | 'socks4' | 'socks5';
export type ProxyAnonymity = 'unknown' | 'transparent' | 'anonymous' | 'elite';

export interface ProxyEndpoint {
  id: string;
  scheme: ProxyScheme;
  host: string;
  port: number;
  username?: string | null;
  source: string;
  country?: string | null;
  asn?: string | null;
  anonymity: ProxyAnonymity;
  latency_ms?: number | null;
  success_count: number;
  fail_count: number;
  score: number;
  last_checked_at?: string | null;
  last_success_at?: string | null;
  last_error?: string | null;
  status: ProxyPool;
}
```

### Stats

```ts
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
  redis_status: 'ok' | 'error' | 'unknown';
  scheduler_status: 'running' | 'stopped' | 'unknown';
}
```

## 9. Required UX Behaviors

1. Every table must support loading, empty, and error states.
2. Proxy list must support pagination.
3. Filters must be reflected in the URL query string if using Next.js.
4. Dangerous actions such as delete must show a confirmation dialog.
5. All backend errors must show a readable message.
6. The dashboard must be usable without live data via mock mode.
7. Do not expose proxy credentials by default. Mask username/password.
8. Do not log secrets in browser console.

## 10. Safe Feature Boundary

Allowed:

- Monitoring proxy quality
- Viewing latency, score, health and country distribution
- Removing bad proxies
- Triggering authorized fetch/validation jobs
- Viewing anonymization leakage check results
- Exporting internal diagnostics

Disallowed:

- Anti-bot bypass helpers
- CAPTCHA bypass helpers
- Target-specific WAF evasion
- Credential stuffing support
- Fake account automation
- Stealth browser fingerprint manipulation
- Guidance that helps avoid detection by third-party systems

## 11. Implementation Phases

### Dashboard Phase 0: Frontend skeleton

- Create dashboard app
- Add routing
- Add AppShell
- Add mock API client
- Add Overview page with mock metrics
- Add basic tests if project supports frontend tests

### Dashboard Phase 1: Proxy list

- Proxy table
- Filtering
- Pagination
- Detail drawer
- Delete confirmation UI
- Mock data first

### Dashboard Phase 2: API integration

- Typed API client
- Connect `/health`, `/stats`, `/proxy/list`
- Error and loading states
- Environment variable for backend URL

### Dashboard Phase 3: Geo and provider pages

- Geo summary charts
- Provider table
- Validation status page
- Events page

### Dashboard Phase 4: Settings and polish

- Settings page
- Theme support
- Responsive layout
- Documentation
- Docker integration

## 12. Definition of Done

A dashboard task is done only when:

1. UI is implemented.
2. Mock data works.
3. API integration is typed or clearly isolated.
4. Loading, empty, and error states exist.
5. Dangerous actions require confirmation.
6. Docs are updated.
7. No secrets are exposed.
8. No unsafe features are added.
