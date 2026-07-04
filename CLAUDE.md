# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ProxyPool Architect is a proxy pool management system with a Python/FastAPI backend backed by SQLite and a React/TypeScript frontend dashboard. It fetches proxies from multiple sources (static configs, URL lists, Clash/V2Ray subscriptions, local adapter cores), validates them through protocol/connectivity/anonymity checks, scores them, and serves the best available proxies via a REST API.

## Commands

### Backend (Python)

```bash
# Install dependencies
uv sync

# Run dev server
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Run dev server with background scheduler enabled
SCHEDULER_ENABLED=true uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Run all quality checks
uv run pytest                    # tests (pytest-asyncio, asyncio_mode=auto)
uv run ruff check .              # lint
uv run mypy app                  # type-check (strict: disallow_untyped_defs)

# Run a single test
uv run pytest tests/test_api.py::test_get_proxy_returns_best_proxy_without_password
```

### Frontend (React Dashboard)

```bash
cd dashboard
pnpm install
pnpm dev                         # dev server on http://localhost:5173
pnpm build                       # build for production (output: dashboard/dist/)
pnpm test                        # vitest (src/**/*.test.ts)
```

### Full Stack (Production)

```bash
uv sync
cd dashboard && pnpm install && pnpm build && cd ..
uv run uvicorn app.main:app --port 8000
# Browser: http://localhost:8000 — API + dashboard on one port
```

## Architecture

### Backend (`app/`)

The app is structured in concentric layers. All async code uses `async/await` and all tests use `pytest-asyncio` in auto mode. SQLite is the sole storage backend — no external services required.

```
app/main.py                  ← FastAPI app factory, lifespan, middleware, static file serving
app/core/config.py           ← Settings (pydantic-settings, reads .env)
app/core/scheduler.py        ← APScheduler jobs: fetch_proxies + validate_proxies
app/core/logging.py          ← loguru config (optional JSON structured logs)

app/models/                  ← Pydantic models (proxy, health, api, auth, dashboard, url_import)
app/storage/
  keys.py                    ← POOL_NAMES, SELECTION_POOLS constants
  sqlite_store.py            ← SQLiteStore: all proxy CRUD + session/auth KV storage
  serializers.py             ← JSON serialize/deserialize for ProxyEndpoint

app/providers/               ← Proxy source providers (same as before)
app/validators/              ← Protocol, connectivity, anonymity validators
app/services/                ← Business logic orchestration
app/api/                     ← FastAPI routers (all data routes under /api prefix)
  routes_proxy.py            ← /api/proxy, /api/proxy/list, /api/proxy/{id}, /api/proxy/report
  routes_stats.py            ← /api/stats
  routes_health.py           ← /api/health
  routes_metrics.py          ← /api/metrics
  routes_auth.py             ← /api/auth/login, /api/auth/logout, /api/auth/session
  routes_dashboard_api.py    ← /api/providers, /api/geo, /api/validation, /api/events, /api/settings
```

**API structure:** All data endpoints are under `/api` prefix. Root-level `/health` and `/metrics` redirect to `/api/health` and `/api/metrics` for backward compatibility. The React SPA is served at `/`.

**Proxy lifecycle:** `raw` → validated → `checked` or `elite` (score ≥ MIN_ELITE_SCORE) or `dead` (after 5 consecutive failures). Failed validation moves to `cooldown` pool; expired cooldown proxies are released back to `raw`.

**SQLite data model:** Single `proxies` table with columns for id, pool, score, scheme, anonymity, source, country, and full JSON payload. Indexes on pool+score, scheme, anonymity, source, country for fast filtered queries. Separate `kv_store` table for session affinity and admin auth sessions with TTL support.

### Frontend (`dashboard/`)

React 18 + TypeScript SPA. Uses hash-based routing (`#/overview`, `#/proxies`, etc.), no React Router. Vite for build/dev. Vitest for tests. In production, FastAPI serves the built `dashboard/dist/` directly.

```
dashboard/src/
  App.tsx                    ← Root component, hash routing, auth gate, theme toggle
  types.ts                   ← TypeScript interfaces matching backend API responses
  lib/
    api-client.ts            ← DashboardApiClient with live/mock mode switching
    mock-data.ts             ← In-memory mock data for offline dev
  i18n/                      ← Chinese/English translations via React context
  pages/                     ← Overview, Proxies, Geo, Providers, Validation, Logs, Settings, Login
  components/                ← Reusable UI components
```

**Data mode:** `VITE_DASHBOARD_DATA_MODE=live` hits the backend API at `VITE_API_BASE_URL` (default `/api`); `mock` (default for local dev) uses in-memory fixtures.

## Key Design Decisions

- **Tests use temp-file SQLite databases**, not in-memory shared databases. Each test creates its own `SQLiteStore(tempfile.mktemp(suffix=".db"))` to avoid locking conflicts.
- **Settings are frozen at import time** via `@lru_cache` on `get_settings()`. Tests that need different settings must import `Settings` directly.
- **All list-type env vars** (e.g. `CORS_ALLOWED_ORIGINS`, `PROVIDER_STATIC_PROXIES`) accept both JSON arrays and comma-separated strings.
- **Proxy credentials are never exposed** in API responses — `password` and `username` are masked; the response includes `auth_required: bool` instead.
- **YAML provider config** (`config/providers.yaml`) is git-ignored because it may contain subscription URLs/credentials. Use `config/providers.yaml.example` as the template.
- **Scheduler is disabled by default** (`SCHEDULER_ENABLED=false`) to keep tests and API-only runs network-free.
- **DB_PATH** configures the SQLite database file location (default: `data/proxy_pool.db`).
- **Ruff lint rules:** B, E, F, I, SIM, UP. Line length 100. Python 3.11 target.
