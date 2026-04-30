# ProxyPool Architect

ProxyPool Architect is a modern Python proxy pool system built with FastAPI and Redis.
This repository is intended for lawful, authorized networking, testing, and proxy quality
management workflows only.

## Current Scope

The current implementation contains the Phase 0 application skeleton, Phase 1 storage
foundation, Phase 2 provider system, Phase 3 validation layer, Phase 4 API service, and
Phase 5 scheduler integration, Phase 6 basic dashboard, and Phase 7 production basics:

- FastAPI application entrypoint at `app/main.py`
- typed `/health` endpoint
- settings via `pydantic-settings`
- loguru logging setup
- Redis service in Docker Compose
- pytest, ruff, and mypy configuration
- `ProxyEndpoint` and `ProxyFilters` models
- Redis key helpers and JSON serialization
- `RedisStore` operations for `raw`, `checked`, `elite`, `dead`, and `cooldown` pools
- score-based best-proxy selection from `elite` then `checked`
- proxy URL parsing for HTTP, HTTPS, SOCKS4, and SOCKS5 sources
- `StaticProvider`, `UrlListProvider`, `ProviderManager`, and `FetchService`
- `ProtocolValidator`, `ConnectivityValidator`, and `AnonymityValidator`
- `ValidateService` with bounded concurrency, scoring, and pool movement
- cooldown handling for failed proxies and scheduled release back to `raw`
- optional `session_id` affinity for stable per-task proxy selection
- `/proxy`, `/proxy/list`, `/proxy/report`, `/stats`, and `DELETE /proxy/{proxy_id}` APIs
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
  "redis_configured": true
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
- `get_best_proxy(filters)`
- `update_score(proxy_id, score_delta)`
- `count_by_pool()`

Redis keys are centralized in `app/storage/keys.py`, and proxy records are stored as JSON.

## Provider Layer

Phase 2 adds provider fetching without proxy validation:

- `StaticProvider` parses configured proxy URLs from `PROVIDER_STATIC_PROXIES`.
- `UrlListProvider` fetches configured text URLs from `PROVIDER_URL_LIST_URLS`.
- `ProviderManager` calls enabled providers.
- `FetchService` deduplicates fetched proxies and writes them to the `raw` pool.

URL list fetching uses configured timeouts and bounded concurrency. It does not retry,
validate, score, or attempt to bypass remote access controls.

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

## Dashboard

Phase 6 adds a lightweight server-rendered dashboard at:

```bash
http://localhost:8000/dashboard
```

It shows pool counts, provider source distribution, average latency, success rate, and a proxy
table with delete actions. It uses the existing API and storage services and does not add a
frontend framework dependency.

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
| `LOG_LEVEL` | `INFO` | Application log level |
| `LOG_JSON` | `false` | Emit structured JSON logs |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection URL |
| `PROVIDER_STATIC_ENABLED` | `true` | Enable static proxy provider |
| `PROVIDER_STATIC_PROXIES` | `[]` | JSON array of static proxy URLs |
| `PROVIDER_URL_LISTS_ENABLED` | `false` | Enable URL list provider |
| `PROVIDER_URL_LIST_URLS` | `[]` | JSON array of text proxy list URLs |
| `PROVIDER_URL_TIMEOUT_SECONDS` | `10` | Timeout for provider URL requests |
| `PROVIDER_URL_CONCURRENCY` | `5` | Max concurrent provider URL requests |
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
| `METRICS_ENABLED` | `true` | Enable `/metrics` endpoint |

## Safety Boundary

Do not use this project for CAPTCHA bypass, anti-bot evasion, credential abuse, account
automation, spam, target-specific block circumvention, or attacks against third-party systems.
