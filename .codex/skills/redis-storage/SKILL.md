---
name: redis-storage
description: Use this skill when implementing Redis data access, proxy pool indexes, serialization, or scoring.
---

# Redis Storage Skill

Rules:

1. Keep Redis key names centralized in app/storage/keys.py.
2. Use JSON serialization for ProxyEndpoint objects unless there is a clear reason not to.
3. Maintain indexes consistently when moving proxies between pools.
4. Prefer sorted sets when selecting by score.
5. Add tests for add, remove, move, list, count, and best-proxy retrieval.
6. Handle missing keys gracefully.
