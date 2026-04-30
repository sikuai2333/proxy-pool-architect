# AGENTS.md

## Project

This project is ProxyPool Architect, a modern Python proxy pool system.

The project must be used only for authorized, lawful, and ethical networking, testing, and scraping scenarios. Do not implement features whose purpose is credential abuse, spam, bypassing anti-bot systems, account creation abuse, or attacking third-party systems.

## Tech Stack

- Python 3.11+
- FastAPI
- Redis
- aiohttp or httpx
- APScheduler
- pydantic-settings
- loguru
- pytest
- pytest-asyncio
- ruff
- mypy
- Docker Compose

## Architecture

Main directories:

- app/api: FastAPI routes
- app/core: config, logging, scheduler, common infrastructure
- app/models: pydantic models
- app/providers: proxy source providers
- app/validators: proxy validation logic
- app/storage: Redis persistence
- app/services: business logic
- tests: unit and integration tests
- docs: design documents

## Engineering Rules

1. Keep modules small and focused.
2. Use async I/O for network-heavy operations.
3. Add tests for every new service and validator.
4. Do not hard-code external endpoints except default test URLs in config.
5. Do not commit secrets, API keys, paid proxy credentials, cookies, or tokens.
6. Prefer typed Python.
7. Use pydantic models for data boundaries.
8. All public APIs must have clear response schemas.
9. Keep README updated when adding commands or endpoints.
10. Avoid adding heavy dependencies unless justified.

## Safety Rules

Do not add:

- CAPTCHA bypass
- anti-bot evasion
- WAF bypass
- credential stuffing logic
- account registration automation
- target-specific rate limit bypass
- exploit or attack modules

Allowed:

- proxy availability checks
- anonymity leakage checks
- latency checks
- protocol support checks
- authorized crawling support
- local and self-owned infrastructure testing

## Commands

Install dependencies:

```bash
uv sync
```

Run development server:

```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Run tests:

```bash
uv run pytest
```

Lint:

```bash
uv run ruff check .
```

Format:

```bash
uv run ruff format .
```

Type check:

```bash
uv run mypy app
```

Docker:

```bash
docker compose up -d
```

## Definition of Done

A task is done only when:

1. Code is implemented.
2. Tests are added or updated.
3. `pytest` passes.
4. `ruff check .` passes.
5. Public APIs are documented.
6. README or docs are updated if behavior changed.
7. No secrets are introduced.
8. The implementation follows the project safety rules.

## How to Work

Before coding:

1. Inspect the current repository.
2. Summarize the relevant files.
3. Propose a short implementation plan.
4. Implement the smallest complete change.
5. Run tests and lint.
6. Provide a concise summary and list changed files.
