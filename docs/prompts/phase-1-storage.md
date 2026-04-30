# Phase 1 Prompt：Redis 存储

```text
Implement Phase 1: data models and Redis storage.

Scope:
1. Add ProxyEndpoint model.
2. Add RedisStore abstraction.
3. Implement raw_pool, checked_pool, elite_pool, dead_pool operations.
4. Add proxy serialization/deserialization.
5. Add score-based retrieval from elite_pool and checked_pool.
6. Add tests using a Redis test container or mocked Redis if necessary.

Required operations:
- add_proxy(pool, proxy)
- get_proxy(proxy_id)
- remove_proxy(pool, proxy_id)
- move_proxy(from_pool, to_pool, proxy_id)
- list_proxies(pool, limit, offset)
- get_best_proxy(filters)
- update_score(proxy_id, score_delta)
- count_by_pool()

Do not implement provider fetching yet.

Run:
- pytest
- ruff check .
- mypy app
```
