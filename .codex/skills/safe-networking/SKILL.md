---
name: safe-networking
description: Use this skill whenever implementing networking, proxy, scraping, or validation features.
---

# Safe Networking Skill

When implementing networking features:

Allowed:

- proxy connectivity testing
- proxy protocol validation
- latency measurement
- anonymity leakage detection
- health checks
- rate limits and cooldowns
- authorized API access
- robots.txt-aware crawling support

Disallowed:

- CAPTCHA bypass
- anti-bot evasion
- WAF bypass
- credential stuffing
- fake account registration
- stealth browser fingerprint manipulation
- target-specific block circumvention
- abusive retry loops

Implementation rules:

1. Add timeouts to all network requests.
2. Add concurrency limits.
3. Respect configured rate limits.
4. Stop retrying when a target returns CAPTCHA, 403, or abuse signals.
5. Log enough information for debugging, but never log secrets.
6. Keep all endpoints configurable.
