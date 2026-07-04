# ProxyPool Architect

ProxyPool Architect is a modern Python proxy pool system built with FastAPI and SQLite.
This repository is intended for lawful, authorized networking, testing, and proxy quality
management workflows only.

## Current Scope

The current implementation contains the Phase 0 application skeleton, Phase 1 storage
foundation, Phase 2 provider system, Phase 3 validation layer, Phase 4 API service, and
Phase 5 scheduler integration, Phase 6 basic dashboard, Phase 7 production basics, and
Phase 8 admin authentication:

- FastAPI application entrypoint at `app/main.py`
- typed `/api/health` endpoint
- settings via `pydantic-settings`
- loguru logging setup
- SQLite storage backend (no external services required)
- pytest, ruff, and mypy configuration
- `ProxyEndpoint` and `ProxyFilters` models
- SQLite-backed proxy CRUD with indexed filtered queries
- score-based best-proxy selection from `elite` then `checked`
- proxy URL parsing for HTTP, HTTPS, SOCKS4, and SOCKS5 sources
- `StaticProvider`, `UrlListProvider`, `ProviderManager`, and `FetchService`
- dashboard-triggered URL import with auto-detected plain text, Clash/FlClash, and V2Ray/Xray subscriptions
- YAML-driven Provider configuration with dynamic trusted provider loading
- Clash/FlClash subscription parsing for HTTP/SOCKS nodes and local Tor SOCKS Provider
- CoreAdapter Provider for Clash/Mihomo/sing-box style local adapter cores
- local CIDR-based Geo enrichment for country and ASN fields
- `ProtocolValidator`, `ConnectivityValidator`, and `AnonymityValidator`
- `ValidateService` with bounded concurrency, scoring, and pool movement
- cooldown handling for failed proxies and scheduled release back to `raw`
- optional `session_id` affinity for stable per-task proxy selection
- `/api/proxy`, `/api/proxy/list`, `/api/proxy/{proxy_id}`, `/api/proxy/report`, `/api/stats`, and `DELETE /api/proxy/{proxy_id}` APIs
- dashboard support APIs for `/api/providers`, `/api/providers/{provider_name}`, `/api/geo/summary`,
  `/api/validation/jobs`, `/api/events`, `/api/settings`, and `PATCH /api/settings`
- admin auth via `/api/auth/session`, `/api/auth/login`, `/api/auth/logout`, browser session cookies,
  and HTTP Basic Auth for direct API clients
- APScheduler-backed fetch and validation jobs, disabled by default
- React dashboard SPA served directly by FastAPI at `/`
- Prometheus-compatible `/api/metrics`, optional JSON logs, and CI workflow

## Setup

Install dependencies:

```bash
uv sync
```

Run the development server:

```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Run the full stack with React dashboard:

```bash
cd dashboard && pnpm install && pnpm build && cd ..
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Check service health:

```bash
curl http://localhost:8000/api/health
```

Expected response:

```json
{
  "status": "ok",
  "app": "ProxyPool Architect",
  "version": "0.1.0",
  "environment": "dev",
  "db_configured": true,
  "db": "ok",
  "scheduler": "stopped"
}
```

## Quality Checks

```bash
uv run pytest
uv run ruff check .
uv run mypy app
```

## Storage Layer

The storage layer uses SQLite with `aiosqlite`:

- `add_proxy(pool, proxy)`
- `get_proxy(proxy_id)`
- `remove_proxy(pool, proxy_id)`
- `move_proxy(from_pool, to_pool, proxy_id)`
- `list_proxies(pool, limit, offset)`
- `list_filtered_proxies(pool, filters, limit, offset)`
- `get_best_proxy(filters)`
- `update_score(proxy_id, score_delta)`
- `count_by_pool()`

The `proxies` table stores proxy data with indexed columns for pool, score, scheme, anonymity,
source, and country. A separate `kv_store` table handles session affinity and admin auth sessions
with TTL support. The database file location is configured via `DB_PATH` (default: `data/proxy_pool.db`).

## Provider Layer

Provider fetching runs without proxy validation:

- `StaticProvider` parses configured proxy URLs from `PROVIDER_STATIC_PROXIES`.
- `UrlListProvider` fetches configured text URLs from `PROVIDER_URL_LIST_URLS`.
- dashboard URL import accepts an on-demand `http`/`https` source URL, auto-detects plain text,
  Clash/FlClash YAML, and V2Ray/Xray subscription payloads, classifies direct vs
  adapter-required nodes, and writes unique direct proxies into `raw`.
- `ClashSubscriptionProvider` parses Clash/FlClash YAML subscriptions, V2Ray/Xray URI lists,
  and text lists for HTTP/SOCKS endpoints.
- `TorProvider` registers an already-running local Tor SOCKS endpoint.
- `CoreAdapterProvider` starts or connects to a local adapter core and registers its local
  HTTP/SOCKS inbound as a normal pool proxy.
- `ProviderManager` calls enabled providers.
- `FetchService` deduplicates fetched proxies and writes them to the `raw` pool.

For YAML configuration, copy `config/providers.yaml.example` to `config/providers.yaml`.

## Validation Layer

- `ProtocolValidator` checks supported proxy scheme and endpoint shape.
- `ConnectivityValidator` checks whether a proxy can reach the configured `TEST_URL`.
- `AnonymityValidator` checks configured anonymity test responses for leakage headers.
- `ValidateService` validates proxies with a bounded semaphore and moves them from `raw` to
  `checked`, `elite`, or `dead` based on validation results and score.

## Cooldown

Failed validation moves proxies into the `cooldown` pool unless the proxy has reached the dead
threshold. Repeated failures with `consecutive_fail_count >= 5` move a proxy to `dead`.

The scheduler releases expired cooldown proxies back to `raw` before each validation run. The
cooldown duration is controlled by `COOLDOWN_SECONDS`.

## API

All data API endpoints are under the `/api` prefix.

Get one proxy as JSON:

```bash
curl "http://localhost:8000/api/proxy?scheme=http&country=US&min_score=80"
```

Use session affinity for task-level stable proxy selection:

```bash
curl "http://localhost:8000/api/proxy?session_id=task-123"
```

Get one proxy as text:

```bash
curl "http://localhost:8000/api/proxy?format=text"
```

List proxies:

```bash
curl "http://localhost:8000/api/proxy/list?pool=checked&limit=50&offset=0"
```

Get proxy details:

```bash
curl "http://localhost:8000/api/proxy/http-1.2.3.4-8080"
```

Report usage result:

```bash
curl -X POST "http://localhost:8000/api/proxy/report" \
  -H "Content-Type: application/json" \
  -d '{"proxy_id":"http-1.2.3.4-8080","ok":true,"latency_ms":120,"error":null}'
```

Get stats:

```bash
curl "http://localhost:8000/api/stats"
```

Delete a proxy:

```bash
curl -X DELETE "http://localhost:8000/api/proxy/http-1.2.3.4-8080"
```

Admin auth via HTTP Basic:

```bash
curl -u "admin:replace-me" "http://localhost:8000/api/stats"
```

Import proxies from a remote text list:

```bash
curl -X POST "http://localhost:8000/api/providers/import-url" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com/http.txt","file_type":"auto"}'
```

## Scheduler

Phase 5 adds APScheduler integration for background fetch and validation work. The scheduler is
disabled by default.

Enable it explicitly:

```bash
SCHEDULER_ENABLED=true uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Metrics And Logs

Prometheus-compatible metrics are available at:

```bash
curl http://localhost:8000/api/metrics
```

Enable JSON logs for log collectors:

```bash
LOG_JSON=true uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Dashboard

The React dashboard is served directly by FastAPI at `http://localhost:8000/`. Build it first:

```bash
cd dashboard && pnpm install && pnpm build
```

For frontend development with hot reload:

```bash
cd dashboard && pnpm dev
```

The development server listens on `http://localhost:5173`. When auth is enabled and the frontend
runs on a different origin, keep `CORS_ALLOWED_ORIGINS` aligned.

## CI

GitHub Actions is configured in `.github/workflows/ci.yml` to run:

- `uv run ruff check .`
- `uv run mypy app`
- `uv run pytest`
- `pnpm install && pnpm build` (frontend)

## Security

See `docs/security.md` for operational boundaries and deployment guidance.

## Configuration

Configuration is read from environment variables or a local `.env` file. Use `.env.example`
as the starting point.

| Variable | Default | Description |
| --- | --- | --- |
| `APP_ENV` | `dev` | Application environment label |
| `APP_HOST` | `0.0.0.0` | Host used by local run commands |
| `APP_PORT` | `8000` | Port used by local run commands |
| `DB_PATH` | `data/proxy_pool.db` | SQLite database file path |
| `AUTH_ENABLED` | `false` | Enable admin authentication |
| `AUTH_ADMIN_USERNAME` | empty | Admin username |
| `AUTH_ADMIN_PASSWORD` | empty | Admin password |
| `AUTH_SESSION_TTL_SECONDS` | `43200` | Session cookie lifetime |
| `AUTH_SESSION_COOKIE_NAME` | `proxy_pool_session` | Cookie name |
| `AUTH_SESSION_SECURE` | `false` | Mark session cookie as HTTPS-only |
| `AUTH_SESSION_SAMESITE` | `lax` | Session cookie SameSite policy |
| `CORS_ALLOWED_ORIGINS` | `["http://localhost:5173","http://127.0.0.1:5173"]` | Allowed CORS origins |
| `CORS_ALLOW_CREDENTIALS` | `false` | Include credentials in CORS |
| `ALLOWED_HOSTS` | `[]` | Optional trusted hostnames |
| `GZIP_MINIMUM_SIZE` | `1024` | Minimum response size for gzip |
| `LOG_LEVEL` | `INFO` | Application log level |
| `LOG_JSON` | `false` | Emit structured JSON logs |
| `PROVIDER_STATIC_ENABLED` | `true` | Enable static proxy provider |
| `PROVIDER_STATIC_PROXIES` | `[]` | JSON array of static proxy URLs |
| `PROVIDER_URL_LISTS_ENABLED` | `false` | Enable URL list provider |
| `PROVIDER_URL_LIST_URLS` | `[]` | JSON array of text proxy list URLs |
| `PROVIDER_URL_TIMEOUT_SECONDS` | `10` | Timeout for provider URL requests |
| `PROVIDER_URL_CONCURRENCY` | `5` | Max concurrent provider URL requests |
| `PROVIDER_CONFIG_FILE` | `config/providers.yaml` | Optional YAML provider config |
| `GEO_ENABLED` | `false` | Enable local CIDR Geo enrichment |
| `GEO_FILE` | `config/geo.csv` | Local Geo CSV file |
| `VALIDATE_CONCURRENCY` | `100` | Max concurrent proxy validations |
| `VALIDATE_TIMEOUT_SECONDS` | `10` | Timeout for validator HTTP requests |
| `TEST_URL` | `https://httpbin.org/ip` | Connectivity test endpoint |
| `ANONYMITY_TEST_URL` | `https://httpbin.org/headers` | Anonymity test endpoint |
| `MIN_ELITE_SCORE` | `80` | Minimum score for `elite` pool |
| `COOLDOWN_SECONDS` | `1800` | Cooldown duration after failure |
| `SESSION_AFFINITY_TTL_SECONDS` | `3600` | TTL for session proxy affinity |
| `SCHEDULER_ENABLED` | `false` | Enable background scheduler |
| `FETCH_INTERVAL_SECONDS` | `1800` | Fetch job interval |
| `VALIDATE_INTERVAL_SECONDS` | `600` | Validation job interval |
| `VALIDATE_BATCH_SIZE` | `100` | Max raw proxies validated per job run |
| `METRICS_ENABLED` | `true` | Enable `/api/metrics` endpoint |

## Safety Boundary

Do not use this project for CAPTCHA bypass, anti-bot evasion, credential abuse, account
automation, spam, target-specific block circumvention, or attacks against third-party systems.
