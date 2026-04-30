# Phase 4 Prompt：API 服务

```text
Implement Phase 4: FastAPI routes.

Endpoints:
1. GET /health
2. GET /proxy
3. GET /proxy/list
4. POST /proxy/report
5. GET /stats
6. DELETE /proxy/{proxy_id}

Requirements:
- Pydantic request and response models
- Filtering by scheme, anonymity, country, min_score
- format=text support for /proxy
- Tests for each endpoint
- Update README API section

Run:
- pytest
- ruff check .
- mypy app
```
