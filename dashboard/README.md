# ProxyPool Architect Dashboard

This is the React dashboard for ProxyPool Architect. It currently includes the Phase 0 shell, the
Phase 1 Proxies workflow, the Phase 2 live API client, and the Phase 3 Geo, Providers, Validation,
and Logs pages. It runs in mock mode by default and can switch to live backend mode.

## Commands

```bash
pnpm install
pnpm dev
pnpm build
pnpm lint
pnpm test
```

The local dev server listens on:

```text
http://localhost:5173
```

## Environment

```env
VITE_DASHBOARD_DATA_MODE=mock
VITE_API_BASE_URL=http://localhost:8000
VITE_API_REQUEST_TIMEOUT_MS=4000
```

The dashboard client lives in `src/lib/api-client.ts`. Mock mode uses payloads from
`src/lib/mock-data.ts`.

Set `VITE_DASHBOARD_DATA_MODE=live` to connect the dashboard to a running backend. The current
backend supports `/health`, `/stats`, `/proxy/list`, `/proxy/{proxy_id}`,
`DELETE /proxy/{proxy_id}`, `/providers`, `/geo/summary`, `/validation/jobs`, `/events`,
`/settings`, and `PATCH /settings`.

## Current Phase 1 Scope

- Overview page with mock metrics
- Proxies page with filters
- Pagination
- Proxy detail drawer
- Mock delete confirmation flow

## Current Phase 3 Scope

- Geo page with country distribution and ASN summary
- Providers page with provider status table
- Validation page with job history and common error types
- Logs page with event history

## Current Phase 4 Scope

- Settings page with safe runtime controls
- Theme toggle with local persistence
- Language toggle with local persistence
- English and Chinese dashboard text resources under `src/i18n`
- Live runtime settings integration with backend fallback compatibility

## Dashboard Guide

1. Use `Overview` for pool health and aggregate quality metrics.
2. Use `Proxies` for filtering, paging, inspecting, and deleting proxies.
3. Use `Geo` and `Providers` to understand where proxies come from and how they perform.
4. Use `Validation` and `Logs` to review failures, timeout patterns, and recent events.
5. Use `Settings` to switch the dashboard language between English and Chinese.

## Deployment

Build static assets:

```bash
pnpm build
```

The production bundle is emitted to `dashboard/dist/`. It can be served by any static file server
or mounted behind the backend in a later integration step.
