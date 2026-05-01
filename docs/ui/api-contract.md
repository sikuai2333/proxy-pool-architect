# Dashboard API Contract

This file describes the API endpoints expected by the ProxyPool Architect dashboard.

If the backend does not implement these endpoints yet, the dashboard should support mock mode and clearly mark missing integrations as TODO.

## Base URL

Frontend env variable:

- `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000`
- or `VITE_API_BASE_URL=http://localhost:8000`

## Endpoints

### GET /auth/session

Response when auth is disabled:

```json
{
  "enabled": false,
  "authenticated": false,
  "username": null,
  "expires_at": null,
  "auth_method": "disabled"
}
```

Response when auth is enabled and the browser session is valid:

```json
{
  "enabled": true,
  "authenticated": true,
  "username": "admin",
  "expires_at": "2026-05-01T12:00:00+08:00",
  "auth_method": "session"
}
```

### POST /auth/login

Request:

```json
{
  "username": "admin",
  "password": "replace-me"
}
```

Response:

```json
{
  "enabled": true,
  "authenticated": true,
  "username": "admin",
  "expires_at": "2026-05-01T12:00:00+08:00",
  "auth_method": "session"
}
```

The backend also sets an `HttpOnly` session cookie for subsequent dashboard requests.

### POST /auth/logout

Response:

```json
{
  "enabled": true,
  "authenticated": false,
  "username": null,
  "expires_at": null,
  "auth_method": null
}
```

### GET /health

Response:

```json
{
  "status": "ok",
  "redis": "ok",
  "scheduler": "running"
}
```

### GET /stats

Response:

```json
{
  "raw": 1200,
  "checked": 320,
  "elite": 58,
  "dead": 900,
  "cooldown": 12,
  "avg_latency_ms": 1380,
  "success_rate": 0.73,
  "last_fetch_at": "2026-04-30T12:00:00+08:00",
  "last_validate_at": "2026-04-30T12:05:00+08:00",
  "redis_status": "ok",
  "scheduler_status": "running"
}
```

### GET /proxy/list

Query params:

- `pool`: raw | checked | elite | dead | cooldown
- `scheme`: http | https | socks4 | socks5
- `anonymity`: unknown | transparent | anonymous | elite
- `country`: string
- `source`: string
- `min_score`: number
- `q`: host or IP search
- `limit`: number
- `offset`: number

Response:

```json
{
  "items": [],
  "total": 0,
  "limit": 50,
  "offset": 0
}
```

### GET /proxy/{proxy_id}

Response:

```json
{
  "id": "socks5-1.2.3.4-1080",
  "scheme": "socks5",
  "host": "1.2.3.4",
  "port": 1080,
  "username": null,
  "source": "url_list_provider",
  "country": "US",
  "asn": "AS12345",
  "anonymity": "elite",
  "latency_ms": 820,
  "success_count": 12,
  "fail_count": 1,
  "score": 91,
  "last_checked_at": "2026-04-30T12:00:00+08:00",
  "last_success_at": "2026-04-30T12:00:00+08:00",
  "last_error": null,
  "status": "elite"
}
```

### DELETE /proxy/{proxy_id}

Response:

```json
{
  "ok": true
}
```

### GET /providers

Response:

```json
{
  "items": [
    {
      "name": "url_list_provider",
      "enabled": true,
      "last_fetch_at": "2026-04-30T12:00:00+08:00",
      "fetched_count": 1000,
      "valid_count": 120,
      "last_error": null
    }
  ]
}
```

### GET /geo/summary

Response:

```json
{
  "coverage": {
    "total_proxies": 3200,
    "geo_tagged_proxies": 2140,
    "unresolved_proxies": 1060,
    "geo_enabled": true,
    "geo_file": "config/geo.csv",
    "geo_file_exists": true
  },
  "countries": [
    {"country": "US", "total": 120, "elite": 32, "avg_latency_ms": 820}
  ],
  "asns": [
    {"asn": "AS12345", "total": 42, "elite": 10, "avg_latency_ms": 910}
  ]
}
```

### GET /validation/jobs

Query:

- `limit` default `50`, max `500`
- `offset` default `0`

Response:

```json
{
  "items": [
    {
      "id": "job-001",
      "started_at": "2026-04-30T12:00:00+08:00",
      "finished_at": "2026-04-30T12:03:00+08:00",
      "checked_count": 500,
      "success_count": 130,
      "fail_count": 370,
      "timeout_count": 42,
      "status": "finished"
    }
  ],
  "total": 18,
  "limit": 10,
  "offset": 0
}
```

### GET /events

Query:

- `limit` default `50`, max `500`
- `offset` default `0`

Response:

```json
{
  "items": [
    {
      "id": "event-001",
      "type": "validation_failed",
      "level": "warning",
      "message": "Proxy timed out during validation",
      "created_at": "2026-04-30T12:00:00+08:00"
    }
  ],
  "total": 128,
  "limit": 20,
  "offset": 0
}
```

## Security and Privacy

- Protected dashboard and management endpoints should require either a valid session cookie or
  HTTP Basic Auth when backend auth is enabled.
- Do not return proxy passwords unless explicitly required by an authenticated internal admin feature.
- Mask credentials in the UI by default.
- Do not log proxy credentials in frontend console.
- Do not add features for anti-bot bypass, CAPTCHA bypass, WAF bypass, stealth automation, or account abuse.
