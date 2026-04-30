# ProxyPool Architect

ProxyPool Architect is a modern Python proxy pool system built with FastAPI and Redis.
This repository is intended for lawful, authorized networking, testing, and proxy quality
management workflows only.

## Current Scope

The current implementation contains the Phase 0 application skeleton and Phase 1 storage
foundation:

- FastAPI application entrypoint at `app/main.py`
- typed `/health` endpoint
- settings via `pydantic-settings`
- loguru logging setup
- Redis service in Docker Compose
- pytest, ruff, and mypy configuration
- `ProxyEndpoint` and `ProxyFilters` models
- Redis key helpers and JSON serialization
- `RedisStore` operations for `raw`, `checked`, `elite`, and `dead` pools
- score-based best-proxy selection from `elite` then `checked`

Providers, validators, scheduler jobs, scoring services, and proxy APIs are planned for later
phases and are not implemented yet.

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

## Configuration

Configuration is read from environment variables or a local `.env` file. Use `.env.example`
as the starting point.

| Variable | Default | Description |
| --- | --- | --- |
| `APP_ENV` | `dev` | Application environment label |
| `APP_HOST` | `0.0.0.0` | Host used by local run commands |
| `APP_PORT` | `8000` | Port used by local run commands |
| `LOG_LEVEL` | `INFO` | Application log level |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection URL for later storage phases |

## Safety Boundary

Do not use this project for CAPTCHA bypass, anti-bot evasion, credential abuse, account
automation, spam, target-specific block circumvention, or attacks against third-party systems.
