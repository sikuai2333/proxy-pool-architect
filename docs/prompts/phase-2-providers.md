# Phase 2 Prompt：Provider 采集模块

```text
Implement Phase 2: provider system.

Scope:
1. Create ProxyProvider base class.
2. Implement StaticProvider from config.
3. Implement UrlListProvider from configured URLs.
4. Implement ProviderManager.
5. Implement FetchService that fetches from enabled providers and writes deduplicated proxies to raw_pool.
6. Add tests for parsing proxy URLs:
   - http://1.2.3.4:8080
   - https://1.2.3.4:8443
   - socks4://1.2.3.4:1080
   - socks5://user:pass@1.2.3.4:1080

Do not implement network validation yet.

Run:
- pytest
- ruff check .
- mypy app
```
