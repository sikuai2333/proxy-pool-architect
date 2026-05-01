# ProxyPool Architect

ProxyPool Architect is a modern Python proxy pool system built with FastAPI and Redis.
This repository is intended for lawful, authorized networking, testing, and proxy quality
management workflows only.

## Current Scope

The current implementation contains the Phase 0 application skeleton, Phase 1 storage
foundation, Phase 2 provider system, Phase 3 validation layer, Phase 4 API service, and
Phase 5 scheduler integration, Phase 6 basic dashboard, Phase 7 production basics, and
Phase 8 admin authentication:

- FastAPI application entrypoint at `app/main.py`
- typed `/health` endpoint
- settings via `pydantic-settings`
- loguru logging setup
- Redis service in Docker Compose
- pytest, ruff, and mypy configuration
- `ProxyEndpoint` and `ProxyFilters` models
- Redis key helpers and JSON serialization
- `RedisStore` operations for `raw`, `checked`, `elite`, `dead`, and `cooldown` pools
- secondary Redis indexes and short-lived list-result caching for filtered proxy queries
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
- `/proxy`, `/proxy/list`, `/proxy/{proxy_id}`, `/proxy/report`, `/stats`, and `DELETE /proxy/{proxy_id}` APIs
- dashboard support APIs for `/providers`, `/providers/{provider_name}`, `/geo/summary`,
  `/validation/jobs`, `/events`, `/settings`, and `PATCH /settings`
- admin auth via `/auth/session`, `/auth/login`, `/auth/logout`, browser session cookies,
  and HTTP Basic Auth for direct API clients
- APScheduler-backed fetch and validation jobs, disabled by default
- lightweight `/dashboard` page for counts, source distribution, latency, success rate, and delete actions
- Prometheus-compatible `/metrics`, optional JSON logs, Docker image hardening, and CI workflow

Advanced production observability and a richer dashboard can be added later.

## Setup

Install dependencies:

```bash
uv sync
```

Run the development server:

```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Run with Docker Compose:

```bash
docker compose up -d
```

Run the production-oriented stack with dashboard + api + redis:

```bash
copy .env.prod.example .env.prod
docker compose -f docker-compose.prod.yml up -d --build
```

Build the Docker image:

```bash
docker build -t proxy-pool-architect:local .
```

Check service health:

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{
  "status": "ok",
  "app": "ProxyPool Architect",
  "version": "0.1.0",
  "environment": "dev",
  "redis_configured": true,
  "redis": "ok",
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

Phase 1 adds the Redis-backed storage abstraction used by later services:

- `add_proxy(pool, proxy)`
- `get_proxy(proxy_id)`
- `remove_proxy(pool, proxy_id)`
- `move_proxy(from_pool, to_pool, proxy_id)`
- `list_proxies(pool, limit, offset)`
- `list_filtered_proxies(pool, filters, limit, offset)`
- `get_best_proxy(filters)`
- `update_score(proxy_id, score_delta)`
- `count_by_pool()`

Redis keys are centralized in `app/storage/keys.py`, and proxy records are stored as JSON.
The storage layer also maintains score-preserving secondary indexes for common list filters
(`scheme`, `anonymity`, `country`, and `source`) plus a global score index. `/proxy/list`
uses those indexes for pagination and exact-match filtering before loading proxy payloads.
Short-lived Redis list caches are invalidated when proxies are added, moved, reported, or deleted.

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
  HTTP/SOCKS inbound as a normal pool proxy, including inferred inbounds from Clash,
  Xray/V2Ray, and sing-box style configs.
- `ProviderManager` calls enabled providers.
- `FetchService` deduplicates fetched proxies and writes them to the `raw` pool.

URL list fetching uses configured timeouts and bounded concurrency. It does not retry,
validate, score, or attempt to bypass remote access controls.
Manual URL import also blocks private or local literal source hosts when
`SAFE_BLOCK_PRIVATE_NETWORKS=true`.

For YAML configuration, copy `config/providers.yaml.example` to `config/providers.yaml`.
The real config file is ignored by Git because it may contain subscription URLs or credentials.
See `docs/providers.md` for the schema and dynamic plugin rules.

For VMess, VLESS, Trojan, Shadowsocks, Hysteria, TUIC, WireGuard, and similar protocols, the
import and provider layers classify those nodes as `core_adapter` traffic. Use a CoreAdapter
config for Mihomo, FlClash, Xray/V2Ray, or sing-box. The external core handles those protocols
and exposes a local HTTP/SOCKS port; ProxyPool Architect then validates and serves that local
port through the standard pool.

## Geo Enrichment

Optional Geo enrichment reads a local CSV file with `cidr,country,asn` columns and annotates
fetched proxies before they are stored in `raw`. It only matches literal IP hosts and does not
perform DNS or external Geo API lookups.

## Validation Layer

Phase 3 adds validation for stored proxies:

- `ProtocolValidator` checks supported proxy scheme and endpoint shape.
- `ConnectivityValidator` checks whether a proxy can reach the configured `TEST_URL`.
- `AnonymityValidator` checks configured anonymity test responses for leakage headers such as
  `Via`, `Forwarded`, and `X-Forwarded-For`, plus optional original IP exposure.
- `ValidateService` validates proxies with a bounded semaphore and moves them from `raw` to
  `checked`, `elite`, or `dead` based on validation results and score.

Validation does not implement CAPTCHA bypass, anti-bot evasion, target-specific block
circumvention, or retry loops.

## Cooldown

Failed validation moves proxies into the `cooldown` pool unless the proxy has reached the dead
threshold. Repeated failures with `consecutive_fail_count >= 5` move a proxy to `dead`; a
successful validation or report resets the consecutive failure counter.

The scheduler releases expired cooldown proxies back to `raw` before each validation run. The
cooldown duration is controlled by `COOLDOWN_SECONDS`.

## API

Get one proxy as JSON:

```bash
curl "http://localhost:8000/proxy?scheme=http&country=US&min_score=80"
```

Use session affinity for task-level stable proxy selection:

```bash
curl "http://localhost:8000/proxy?session_id=task-123"
```

When the pinned proxy is still available and matches the filters, the same `session_id` returns
the same proxy until `SESSION_AFFINITY_TTL_SECONDS` expires.

Get one proxy as text:

```bash
curl "http://localhost:8000/proxy?format=text"
```

The text format intentionally omits proxy credentials and returns `scheme://host:port`.

List proxies:

```bash
curl "http://localhost:8000/proxy/list?pool=checked&limit=50&offset=0"
```

List proxies across all pools with source and host search filters:

```bash
curl "http://localhost:8000/proxy/list?source=static&q=1.2.3.4&limit=50&offset=0"
```

The list endpoint is optimized for large pools by using Redis sorted-set indexes for pool,
score, source, scheme, anonymity, and country filters. Host/ID substring search is applied
after indexed filters have narrowed the candidate set.

Get proxy details:

```bash
curl "http://localhost:8000/proxy/http-1.2.3.4-8080"
```

Report usage result:

```bash
curl -X POST "http://localhost:8000/proxy/report" \
  -H "Content-Type: application/json" \
  -d '{"proxy_id":"http-1.2.3.4-8080","ok":true,"latency_ms":120,"error":null}'
```

Get stats:

```bash
curl "http://localhost:8000/stats"
```

Delete a proxy:

```bash
curl -X DELETE "http://localhost:8000/proxy/http-1.2.3.4-8080"
```

Get provider, geo, validation, event, and settings data for the React dashboard:

```bash
curl "http://localhost:8000/providers"
curl "http://localhost:8000/geo/summary"
curl "http://localhost:8000/validation/jobs?limit=20&offset=0"
curl "http://localhost:8000/events?limit=20&offset=0"
curl "http://localhost:8000/settings"
```

Import proxies from a remote text list for the dashboard Providers page:

```bash
curl -X POST "http://localhost:8000/providers/import-url" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com/http.txt","file_type":"http"}'
```

Use `file_type=auto` to auto-detect plain text, Clash/FlClash YAML, and V2Ray/Xray subscription
payloads. `file_type=http` and `file_type=socks5` are still available for bare `host:port`
lists, `file_type=all` accepts mixed direct proxy URLs, and `file_type=clash` / `file_type=v2ray`
force those parser paths.

The response distinguishes direct nodes that are stored into `raw`, adapter-required nodes such
as VMess/VLESS/Trojan/Shadowsocks that need a local core adapter, and unsupported or invalid
entries.

Check the current auth session status:

```bash
curl "http://localhost:8000/auth/session"
```

Log in from a browser or API client to receive a session cookie:

```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"replace-me"}'
```

Use HTTP Basic Auth for direct API calls without a browser session:

```bash
curl -u "admin:replace-me" "http://localhost:8000/stats"
curl -u "admin:replace-me" "http://localhost:8000/proxy/list?pool=elite&limit=20&offset=0"
```

For repeatable live import checks against curated public GitHub proxy sources, this repository
also includes:

```bash
uv run python scripts/import_github_proxy_sources.py
```

The script reads `config/github_proxy_sources.yaml`, calls
`POST /providers/import-url` for each configured source, prints import counts plus pool deltas,
then fetches a sample from `/proxy/list?pool=raw`.

Update safe runtime dashboard settings:

```bash
curl -X PATCH "http://localhost:8000/settings" \
  -H "Content-Type: application/json" \
  -d '{"fetch_interval_seconds":900,"validate_interval_seconds":300,"validate_timeout_seconds":5,"validate_concurrency":50,"min_elite_score":85,"cooldown_seconds":1200,"safe_networking":{"authorized_targets_only":true,"block_private_networks":true,"mask_proxy_credentials":true}}'
```

JSON proxy responses use a public schema and do not include stored proxy passwords.

## Scheduler

Phase 5 adds APScheduler integration for background fetch and validation work. The scheduler is
disabled by default so tests and local API-only runs do not perform network work.

Enable it explicitly:

```bash
SCHEDULER_ENABLED=true uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Registered jobs:

- `fetch_proxies`: runs every `FETCH_INTERVAL_SECONDS` and writes fetched proxies to `raw`.
- `validate_proxies`: runs every `VALIDATE_INTERVAL_SECONDS` and validates at most
  `VALIDATE_BATCH_SIZE` raw proxies per run.

Jobs use `max_instances=1`, coalescing, configured network timeouts, bounded validation
concurrency, and no retry loops.

## Metrics And Logs

Prometheus-compatible metrics are available at:

```bash
curl http://localhost:8000/metrics
```

Metrics include pool counts, total proxies, average latency, success rate, and source
distribution. Metrics do not expose proxy credentials.

Enable JSON logs for log collectors:

```bash
LOG_JSON=true uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Dashboard-facing runtime events and validation jobs are retained in memory with bounded history
and time-based pruning. Docker Compose also enables container log rotation so long-running local
instances do not grow unbounded JSON log files.

## Dashboard

Phase 6 adds a lightweight server-rendered dashboard at:

```bash
http://localhost:8000/dashboard
```

It shows pool counts, provider source distribution, average latency, success rate, and a proxy
table with delete actions. It uses the existing API and storage services and does not add a
frontend framework dependency.

A separate React dashboard app is available under `dashboard/`. It currently includes the Phase 0
shell, the Phase 1 Proxies workflow, the Phase 2 live API client, the Phase 3 Geo, Providers,
Validation, and Logs pages, and the Phase 4 Settings workflow:

```bash
cd dashboard
pnpm install
pnpm dev
```

The frontend development server listens on `http://localhost:5173`.
When auth is enabled and the frontend runs on `http://localhost:5173`, keep
`CORS_ALLOWED_ORIGINS` aligned to that origin and set `CORS_ALLOW_CREDENTIALS=true`
so the browser can send the session cookie.
The Providers page includes a URL submit form that reports detected subscription format,
protocols, direct-supported count, adapter-required count, stored count, duplicate count, and
invalid count after each import.
The Overview page auto-refreshes every 5 seconds, Geo now surfaces coverage and Geo-file status
even when no country or ASN rows are available, and Providers, Validation Jobs, Geo tables, and
Logs all paginate their list views.
When `AUTH_ENABLED=true`, the React dashboard shows a login page first, then uses an
`HttpOnly` session cookie for subsequent `/api/*` requests.

For production Docker deployment, prefer serving the dashboard and API on the same origin through
the dashboard container's bundled Nginx reverse proxy. That keeps browser requests on
`/api/*` and avoids most cross-origin deployment issues entirely.

## CI

GitHub Actions is configured in `.github/workflows/ci.yml` to run:

- `uv run ruff check .`
- `uv run mypy app`
- `uv run pytest`
- `docker build -t proxy-pool-architect:ci .`

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
| `AUTH_ENABLED` | `false` | Enable admin authentication for dashboard and protected APIs |
| `AUTH_ADMIN_USERNAME` | empty | Admin username required when auth is enabled |
| `AUTH_ADMIN_PASSWORD` | empty | Admin password required when auth is enabled |
| `AUTH_SESSION_TTL_SECONDS` | `43200` | Session cookie lifetime in seconds |
| `AUTH_SESSION_COOKIE_NAME` | `proxy_pool_session` | Cookie name used by browser dashboard sessions |
| `AUTH_SESSION_SECURE` | `false` | Mark session cookie as HTTPS-only; set `true` behind TLS |
| `AUTH_SESSION_SAMESITE` | `lax` | Session cookie SameSite policy: `lax`, `strict`, or `none` |
| `CORS_ALLOWED_ORIGINS` | `["http://localhost:5173","http://127.0.0.1:5173"]` | Origins allowed to call the API from the React dashboard dev server |
| `CORS_ALLOW_CREDENTIALS` | `false` | Whether CORS responses include `Access-Control-Allow-Credentials`; required for cross-origin cookie login |
| `ALLOWED_HOSTS` | `[]` | Optional trusted hostnames; use JSON or comma-separated list |
| `GZIP_MINIMUM_SIZE` | `1024` | Minimum response size in bytes before gzip compression is applied |
| `LOG_LEVEL` | `INFO` | Application log level |
| `LOG_JSON` | `false` | Emit structured JSON logs |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection URL |
| `PROXY_LIST_CACHE_TTL_SECONDS` | `10` | Short TTL for Redis-cached `/proxy/list` results; set `0` to disable |
| `PROVIDER_STATIC_ENABLED` | `true` | Enable static proxy provider |
| `PROVIDER_STATIC_PROXIES` | `[]` | JSON array of static proxy URLs |
| `PROVIDER_URL_LISTS_ENABLED` | `false` | Enable URL list provider |
| `PROVIDER_URL_LIST_URLS` | `[]` | JSON array of text proxy list URLs |
| `PROVIDER_URL_TIMEOUT_SECONDS` | `10` | Timeout for provider URL requests |
| `PROVIDER_URL_CONCURRENCY` | `5` | Max concurrent provider URL requests |
| `PROVIDER_CONFIG_FILE` | `config/providers.yaml` | Optional YAML provider config |
| `PROVIDER_PLUGIN_ALLOWED_PREFIXES` | `["app.providers."]` | Allowed dynamic provider class prefixes |
| `GEO_ENABLED` | `false` | Enable local CIDR Geo enrichment |
| `GEO_FILE` | `config/geo.csv` | Local Geo CSV file |
| `VALIDATE_CONCURRENCY` | `100` | Max concurrent proxy validations |
| `VALIDATE_TIMEOUT_SECONDS` | `10` | Timeout for validator HTTP requests |
| `TEST_URL` | `https://httpbin.org/ip` | Connectivity test endpoint |
| `ANONYMITY_TEST_URL` | `https://httpbin.org/headers` | Anonymity leakage test endpoint |
| `VALIDATOR_ORIGINAL_IP` | unset | Optional known client IP for leakage checks |
| `MIN_ELITE_SCORE` | `80` | Minimum score required for `elite` pool |
| `COOLDOWN_SECONDS` | `1800` | Cooldown duration after failed validation/reporting |
| `SESSION_AFFINITY_TTL_SECONDS` | `3600` | TTL for `session_id` proxy affinity |
| `SCHEDULER_ENABLED` | `false` | Enable background scheduler |
| `FETCH_INTERVAL_SECONDS` | `1800` | Fetch job interval |
| `VALIDATE_INTERVAL_SECONDS` | `600` | Validation job interval |
| `VALIDATE_BATCH_SIZE` | `100` | Max raw proxies validated per job run |
| `RUNTIME_EVENT_LIMIT` | `500` | Max in-memory dashboard events retained before trimming |
| `RUNTIME_VALIDATION_JOB_LIMIT` | `200` | Max in-memory validation jobs retained before trimming |
| `RUNTIME_EVENT_RETENTION_SECONDS` | `86400` | Event retention window before expired entries are pruned |
| `RUNTIME_VALIDATION_JOB_RETENTION_SECONDS` | `604800` | Validation-job retention window before expired entries are pruned |
| `METRICS_ENABLED` | `true` | Enable `/metrics` endpoint |
| `SAFE_AUTHORIZED_TARGETS_ONLY` | `true` | Keep runtime controls limited to approved targets |
| `SAFE_BLOCK_PRIVATE_NETWORKS` | `true` | Default safe-networking guard for private ranges |
| `SAFE_MASK_PROXY_CREDENTIALS` | `true` | Keep proxy credentials masked in dashboard responses |

## Production Deployment Notes

You do not need to upload the repository to GitHub just to deploy it.

Common deployment paths:

1. Copy the repository to the server, then run `docker compose -f docker-compose.prod.yml up -d --build`.
2. Build images on your workstation, export them with `docker save`, copy the tar files to the NAS, then `docker load` and start the same compose stack there.
3. Build images in CI and push them to a registry such as GHCR, then run `docker compose pull && docker compose up -d`.

If you want repeatable remote deployment, the registry path is better. GitHub is useful there
because GitHub Actions can build tagged images and publish them to GHCR. But GitHub is not a hard
requirement for Docker deployment itself.

The repository now includes:

- `.env.prod.example`: production environment template
- `docker-compose.prod.yml`: dashboard + api + redis deployment
- `dashboard/Dockerfile` and `dashboard/nginx.conf`: same-origin frontend serving with `/api` reverse proxy
- `docs/nas-deployment-auth.md`: NAS + Docker + login auth deployment guide

Recommended production flow:

1. Copy `.env.prod.example` to `.env.prod` and set your real hostnames.
2. Set `AUTH_ADMIN_USERNAME` and `AUTH_ADMIN_PASSWORD` in `.env.prod`; do not commit the real file.
3. Set `ALLOWED_HOSTS` to your real NAS hostname, internal domain, or reverse-proxy host.
4. If the dashboard and API stay on the same origin via `/api`, keep `CORS_ALLOWED_ORIGINS=[]`.
5. If you split frontend and API across different origins, explicitly set `CORS_ALLOWED_ORIGINS` and `CORS_ALLOW_CREDENTIALS=true`.
6. If the NAS is behind HTTPS, set `AUTH_SESSION_SECURE=true`; keep it `false` for plain HTTP-only LAN testing.
7. Start with `docker compose -f docker-compose.prod.yml up -d --build`.

For NAS deployments without GitHub or a registry, a simple transfer flow is:

```bash
docker build -t proxy-pool-architect:local .
docker build -t proxy-pool-dashboard:local ./dashboard
docker save -o proxy-pool-images.tar proxy-pool-architect:local proxy-pool-dashboard:local redis:7-alpine
```

Copy `proxy-pool-images.tar`, the repository, and `.env.prod` to the NAS, then run:

```bash
docker load -i proxy-pool-images.tar
docker compose -f docker-compose.prod.yml up -d
```

This project is closer to production-ready after the current changes, but it still does not have:

- RBAC beyond a single shared admin account
- HTTPS certificate termination inside the repo
- external secrets manager integration
- centralized metrics/log shipping
- automated image publishing workflow

Those are the main remaining gaps if you want internet-facing production use.

## Safety Boundary

Do not use this project for CAPTCHA bypass, anti-bot evasion, credential abuse, account
automation, spam, target-specific block circumvention, or attacks against third-party systems.
