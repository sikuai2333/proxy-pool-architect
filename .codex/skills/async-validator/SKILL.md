---
name: async-validator
description: Use this skill when implementing async proxy validation, concurrency limits, retries, or scoring.
---

# Async Validator Skill

Rules:

1. Use asyncio with a bounded semaphore.
2. All network requests must have timeouts.
3. Return structured validation results.
4. Never raise raw network exceptions out of the validator.
5. Use scoring rules from PROJECT_PLAN.md.
6. Add tests for success, timeout, connection error, invalid proxy, and transparent proxy.
