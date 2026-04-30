# Security Configuration

ProxyPool Architect is intended for authorized proxy quality management, networking tests, and
lawful crawling workflows.

## Required Boundaries

Do not use this project for:

- CAPTCHA bypass
- anti-bot evasion
- WAF bypass
- credential stuffing
- fake account registration
- spam
- target-specific block circumvention
- exploit or attack activity

## Configuration Guidance

- Keep `SCHEDULER_ENABLED=false` unless background fetching and validation are explicitly needed.
- Configure only proxy sources you are authorized to use.
- Keep `PROVIDER_URL_LISTS_ENABLED=false` unless the configured URLs are trusted and allowed.
- Keep `config/providers.yaml` out of Git; it may contain subscription URLs or credentials.
- Load custom provider classes only from trusted packages.
- Tor support expects a local Tor SOCKS endpoint and does not rotate identities or bypass access
  controls.
- Use conservative `PROVIDER_URL_CONCURRENCY` and `VALIDATE_CONCURRENCY` values.
- Keep `VALIDATE_TIMEOUT_SECONDS` low enough to prevent stuck network work.
- Keep `COOLDOWN_SECONDS` high enough to avoid repeatedly probing failing proxies.
- Set `VALIDATOR_ORIGINAL_IP` only when you intentionally want leakage checks to detect that IP.
- Do not store paid proxy credentials, API tokens, cookies, or secrets in Git.
- Use environment variables or a secrets manager for any production credentials.

## Observability

- `/metrics` exposes aggregate counts, latency, success rate, and provider source labels.
- Metrics do not expose proxy passwords.
- JSON logging can be enabled with `LOG_JSON=true` for log collectors.

## Network Behavior

The application does not perform unbounded retries. Provider fetching and validation use
configured timeouts and concurrency limits. The validation layer detects connectivity and
anonymity leakage; it is not designed to bypass remote protections.
