# Phase 3 Prompt：Validator 检测模块

```text
Implement Phase 3: validators.

Scope:
1. ConnectivityValidator
2. ProtocolValidator
3. AnonymityValidator
4. ValidateService with concurrency limit
5. Move proxies to checked_pool, elite_pool, dead_pool according to validation result.
6. Add scoring rules.
7. Add tests with mocked HTTP responses.

Important:
Anonymity validation is only for detecting leakage such as Via, Forwarded, X-Forwarded-For, or original IP exposure. Do not implement target-specific evasion or anti-bot bypass.

Run:
- pytest
- ruff check .
- mypy app
```
