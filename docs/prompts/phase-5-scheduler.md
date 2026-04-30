# Phase 5 Prompt：调度系统

```text
Implement Phase 5: scheduler system.

Scope:
1. Add APScheduler integration.
2. Schedule fetch jobs by FETCH_INTERVAL_SECONDS.
3. Schedule validation jobs by VALIDATE_INTERVAL_SECONDS.
4. Add startup and shutdown lifecycle hooks.
5. Add structured logs for job start, success, failure, duration.
6. Make scheduler configurable and disableable in tests.
7. Add tests for scheduler registration without running real network jobs.

Rules:
- Do not run unbounded jobs.
- Do not perform infinite retries.
- All jobs must have clear timeout and error handling.

Run:
- pytest
- ruff check .
- mypy app
```
