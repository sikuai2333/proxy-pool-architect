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
`/settings`, `PATCH /settings`, `/auth/session`, `/auth/login`, and `/auth/logout`.

When backend auth is enabled, the dashboard first loads `/auth/session`. If the browser is not
authenticated, the app shows a login screen and stores the returned session only in an
`HttpOnly` cookie. It does not use `localStorage` for auth tokens.

## Current Phase 1 Scope

- Overview page with mock metrics
- Proxies page with filters
- Pagination
- Proxy detail drawer
- Mock delete confirmation flow

## Current Phase 3 Scope

- Geo page with country distribution and ASN summary
- Latency analysis from country and ASN average latency
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

For container deployment, this directory now includes:

- `Dockerfile`: multi-stage build for the React dashboard
- `nginx.conf`: static hosting plus `/api/*` reverse proxy to the backend container named `api`

Build the dashboard image:

```bash
docker build -t proxy-pool-dashboard:local ./dashboard
```

Example compose snippet:

```yaml
services:
  api:
    image: proxy-pool-architect:local
    environment:
      REDIS_URL: redis://redis:6379/0
    depends_on:
      redis:
        condition: service_healthy

  dashboard:
    build:
      context: ./dashboard
      args:
        VITE_DASHBOARD_DATA_MODE: live
        VITE_API_BASE_URL: /api
        VITE_API_REQUEST_TIMEOUT_MS: 4000
    ports:
      - "8080:80"
    depends_on:
      - api

  redis:
    image: redis:7-alpine
```

Then open:

```text
http://localhost:8080
```

Important deployment rule: if the dashboard runs in a browser, `VITE_API_BASE_URL` must point to
an address reachable by that browser. Using `/api` through the bundled Nginx reverse proxy is the
most portable option for Docker deployments.

For local cross-origin development (`http://localhost:5173` -> `http://localhost:8000`) with
cookie-based login, the backend must allow that origin in `CORS_ALLOWED_ORIGINS` and set
`CORS_ALLOW_CREDENTIALS=true`.

When this dashboard is deployed together with the backend through `../docker-compose.prod.yml`,
the recommended browser entrypoint is:

```text
http://<host>:8080
```

and backend requests stay same-origin under:

```text
http://<host>:8080/api/*
```

In that same-origin Docker layout, dashboard login works without extra browser CORS handling.
