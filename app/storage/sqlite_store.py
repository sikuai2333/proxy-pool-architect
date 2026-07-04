from __future__ import annotations

from pathlib import Path
from typing import cast

import aiosqlite

from app.models.proxy import ProxyEndpoint, ProxyFilters, ProxyPool
from app.storage.keys import POOL_NAMES, SELECTION_POOLS
from app.storage.serializers import deserialize_proxy, serialize_proxy

_DB_PATH_DEFAULT = "data/proxy_pool.db"


class SQLiteStore:
    """SQLite-backed proxy store replacing the former RedisStore.

    Implements the same public interface so that all downstream services
    continue to work unchanged.
    """

    def __init__(self, db_path: str = _DB_PATH_DEFAULT) -> None:
        self._db_path = db_path
        self._db: aiosqlite.Connection | None = None

    @classmethod
    def from_path(cls, db_path: str = _DB_PATH_DEFAULT) -> SQLiteStore:
        return cls(db_path=db_path)

    async def _get_db(self) -> aiosqlite.Connection:
        if self._db is None:
            use_uri = self._db_path.startswith("file:")
            if not use_uri and not self._db_path.startswith(":"):
                Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
            self._db = await aiosqlite.connect(self._db_path, uri=use_uri)
            self._db.row_factory = aiosqlite.Row
            await self._db.execute("PRAGMA journal_mode=WAL")
            await self._db.execute("PRAGMA foreign_keys=ON")
            await self._init_tables(self._db)
        return self._db

    async def close(self) -> None:
        if self._db is not None:
            await self._db.close()
            self._db = None

    @staticmethod
    async def _init_tables(db: aiosqlite.Connection) -> None:
        await db.executescript(
            """
            CREATE TABLE IF NOT EXISTS proxies (
                id TEXT PRIMARY KEY,
                pool TEXT NOT NULL,
                score INTEGER NOT NULL DEFAULT 0,
                scheme TEXT,
                anonymity TEXT,
                source TEXT,
                country TEXT,
                payload TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_proxies_pool_score
                ON proxies(pool, score DESC);
            CREATE INDEX IF NOT EXISTS idx_proxies_scheme
                ON proxies(scheme, score DESC);
            CREATE INDEX IF NOT EXISTS idx_proxies_anonymity
                ON proxies(anonymity, score DESC);
            CREATE INDEX IF NOT EXISTS idx_proxies_source
                ON proxies(source, score DESC);
            CREATE INDEX IF NOT EXISTS idx_proxies_country
                ON proxies(country, score DESC);

            CREATE TABLE IF NOT EXISTS kv_store (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                expires_at REAL
            );
            """
        )
        await db.commit()

    # ------------------------------------------------------------------
    # Proxy CRUD
    # ------------------------------------------------------------------

    async def add_proxy(self, pool: ProxyPool, proxy: ProxyEndpoint) -> ProxyEndpoint:
        stored = proxy.model_copy(update={"status": pool})
        await self._upsert_proxy(pool, stored)
        return stored

    async def save_proxy(self, pool: ProxyPool, proxy: ProxyEndpoint) -> ProxyEndpoint:
        stored = proxy.model_copy(update={"status": pool})
        await self._upsert_proxy(pool, stored)
        return stored

    async def get_proxy(self, proxy_id: str) -> ProxyEndpoint | None:
        db = await self._get_db()
        async with db.execute(
            "SELECT payload FROM proxies WHERE id = ?", (proxy_id,)
        ) as cursor:
            row = await cursor.fetchone()
        if row is None:
            return None
        return deserialize_proxy(row["payload"])

    async def remove_proxy(self, pool: ProxyPool, proxy_id: str) -> bool:
        db = await self._get_db()
        async with db.execute(
            "SELECT id FROM proxies WHERE id = ? AND pool = ?", (proxy_id, pool)
        ) as cursor:
            row = await cursor.fetchone()
        if row is None:
            return False
        await db.execute("DELETE FROM proxies WHERE id = ?", (proxy_id,))
        await db.commit()
        return True

    async def delete_proxy(self, proxy_id: str) -> bool:
        db = await self._get_db()
        async with db.execute(
            "SELECT id FROM proxies WHERE id = ?", (proxy_id,)
        ) as cursor:
            row = await cursor.fetchone()
        if row is None:
            return False
        await db.execute("DELETE FROM proxies WHERE id = ?", (proxy_id,))
        await db.commit()
        return True

    async def find_proxy_pool(self, proxy_id: str) -> ProxyPool | None:
        db = await self._get_db()
        async with db.execute(
            "SELECT pool FROM proxies WHERE id = ?", (proxy_id,)
        ) as cursor:
            row = await cursor.fetchone()
        if row is None:
            return None
        pool = row["pool"]
        if pool in POOL_NAMES:
            return cast(ProxyPool, pool)
        return None

    async def get_proxy_record(self, proxy_id: str) -> tuple[ProxyPool, ProxyEndpoint] | None:
        db = await self._get_db()
        async with db.execute(
            "SELECT pool, payload FROM proxies WHERE id = ?", (proxy_id,)
        ) as cursor:
            row = await cursor.fetchone()
        if row is None:
            return None
        pool = row["pool"]
        if pool not in POOL_NAMES:
            return None
        return cast(ProxyPool, pool), deserialize_proxy(row["payload"])

    async def move_proxy(
        self,
        from_pool: ProxyPool,
        to_pool: ProxyPool,
        proxy_id: str,
    ) -> ProxyEndpoint | None:
        db = await self._get_db()
        async with db.execute(
            "SELECT payload FROM proxies WHERE id = ? AND pool = ?",
            (proxy_id, from_pool),
        ) as cursor:
            row = await cursor.fetchone()
        if row is None:
            return None

        proxy = deserialize_proxy(row["payload"]).model_copy(update={"status": to_pool})
        await db.execute(
            "UPDATE proxies SET pool = ?, score = ?, scheme = ?, anonymity = ?, "
            "source = ?, country = ?, payload = ? WHERE id = ?",
            (to_pool, proxy.score, proxy.scheme, proxy.anonymity, proxy.source,
             proxy.country, serialize_proxy(proxy), proxy_id),
        )
        await db.commit()
        return proxy

    async def update_score(self, proxy_id: str, score_delta: int) -> ProxyEndpoint | None:
        located = await self.get_proxy_record(proxy_id)
        if located is None:
            return None
        pool, proxy = located
        updated = proxy.model_copy(update={"score": proxy.score + score_delta})
        await self._upsert_proxy(pool, updated)
        return updated

    # ------------------------------------------------------------------
    # Listing and selection
    # ------------------------------------------------------------------

    async def list_proxies(
        self,
        pool: ProxyPool,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ProxyEndpoint]:
        if limit <= 0:
            return []
        db = await self._get_db()
        async with db.execute(
            "SELECT payload FROM proxies WHERE pool = ? ORDER BY score DESC LIMIT ? OFFSET ?",
            (pool, limit, max(offset, 0)),
        ) as cursor:
            rows = await cursor.fetchall()
        return [deserialize_proxy(row["payload"]) for row in rows]

    async def get_best_proxy(self, filters: ProxyFilters | None = None) -> ProxyEndpoint | None:
        active_filters = filters or ProxyFilters()
        for pool in SELECTION_POOLS:
            candidates, _ = await self.list_filtered_proxies(
                pool=pool,
                filters=active_filters,
                limit=1,
                offset=0,
            )
            if candidates:
                return candidates[0]
        return None

    async def list_filtered_proxies(
        self,
        pool: ProxyPool | None,
        filters: ProxyFilters | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[ProxyEndpoint], int]:
        active_filters = filters or ProxyFilters()
        if limit <= 0:
            return [], 0

        db = await self._get_db()
        where_clauses: list[str] = []
        params: list[object] = []

        if pool is not None:
            where_clauses.append("pool = ?")
            params.append(pool)

        if active_filters.scheme is not None:
            where_clauses.append("scheme = ?")
            params.append(active_filters.scheme)

        if active_filters.anonymity is not None:
            where_clauses.append("anonymity = ?")
            params.append(active_filters.anonymity)

        if active_filters.country is not None:
            where_clauses.append("country = ?")
            params.append(active_filters.country)

        if active_filters.source is not None:
            where_clauses.append("source = ?")
            params.append(active_filters.source)

        if active_filters.min_score is not None:
            where_clauses.append("score >= ?")
            params.append(active_filters.min_score)

        where_sql = " AND ".join(where_clauses) if where_clauses else "1"

        # Count total
        async with db.execute(
            f"SELECT COUNT(*) FROM proxies WHERE {where_sql}", params
        ) as cursor:
            row = await cursor.fetchone()
            total = row[0] if row is not None else 0

        # Fetch page (ordered by score DESC, then id for stability)
        page_params = [*params, limit, max(offset, 0)]
        async with db.execute(
            f"SELECT payload FROM proxies WHERE {where_sql} "
            f"ORDER BY score DESC, id LIMIT ? OFFSET ?",
            page_params,
        ) as cursor:
            rows = await cursor.fetchall()

        proxies = [deserialize_proxy(row["payload"]) for row in rows]

        # Apply host/ID substring filter after SQL filters
        if active_filters.query and active_filters.query.strip():
            query = active_filters.query.strip().casefold()
            proxies = [
                p for p in proxies
                if query in p.host.casefold() or query in p.id.casefold()
            ]
            # Re-count after text filter for accuracy
            if len(proxies) < (limit if offset == 0 else limit + offset):
                total = len(proxies) + offset

        return proxies, total

    async def count_by_pool(self) -> dict[ProxyPool, int]:
        db = await self._get_db()
        counts: dict[ProxyPool, int] = {pool: 0 for pool in POOL_NAMES}
        async with db.execute(
            "SELECT pool, COUNT(*) as cnt FROM proxies GROUP BY pool"
        ) as cursor:
            async for row in cursor:
                pool = row["pool"]
                if pool in counts:
                    counts[pool] = row["cnt"]
        return counts

    async def list_all_proxies(self) -> list[ProxyEndpoint]:
        db = await self._get_db()
        async with db.execute(
            "SELECT payload FROM proxies ORDER BY score DESC"
        ) as cursor:
            rows = await cursor.fetchall()
        return [deserialize_proxy(row["payload"]) for row in rows]

    # ------------------------------------------------------------------
    # Session affinity
    # ------------------------------------------------------------------

    async def bind_session_proxy(
        self,
        session_id: str,
        proxy_id: str,
        ttl_seconds: int,
    ) -> None:
        from time import time

        expires_at = time() + ttl_seconds
        db = await self._get_db()
        await db.execute(
            "INSERT OR REPLACE INTO kv_store (key, value, expires_at) VALUES (?, ?, ?)",
            (f"session:{session_id}", proxy_id, expires_at),
        )
        await db.commit()

    async def get_session_proxy_id(self, session_id: str) -> str | None:
        from time import time

        db = await self._get_db()
        now = time()
        async with db.execute(
            "SELECT value, expires_at FROM kv_store WHERE key = ?",
            (f"session:{session_id}",),
        ) as cursor:
            row = await cursor.fetchone()
        if row is None:
            return None
        if row["expires_at"] is not None and row["expires_at"] < now:
            await db.execute("DELETE FROM kv_store WHERE key = ?", (f"session:{session_id}",))
            await db.commit()
            return None
        return row["value"]

    # ------------------------------------------------------------------
    # Admin sessions
    # ------------------------------------------------------------------

    async def save_admin_session(self, token: str, payload: str, ttl_seconds: int) -> None:
        from time import time

        expires_at = time() + ttl_seconds
        db = await self._get_db()
        await db.execute(
            "INSERT OR REPLACE INTO kv_store (key, value, expires_at) VALUES (?, ?, ?)",
            (f"admin_session:{token}", payload, expires_at),
        )
        await db.commit()

    async def get_admin_session(self, token: str) -> str | None:
        from time import time

        db = await self._get_db()
        now = time()
        async with db.execute(
            "SELECT value, expires_at FROM kv_store WHERE key = ?",
            (f"admin_session:{token}",),
        ) as cursor:
            row = await cursor.fetchone()
        if row is None:
            return None
        if row["expires_at"] is not None and row["expires_at"] < now:
            await db.execute(
                "DELETE FROM kv_store WHERE key = ?", (f"admin_session:{token}",)
            )
            await db.commit()
            return None
        return row["value"]

    async def delete_admin_session(self, token: str) -> bool:
        db = await self._get_db()
        result = await db.execute(
            "DELETE FROM kv_store WHERE key = ?", (f"admin_session:{token}",)
        )
        await db.commit()
        return result.rowcount > 0

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _upsert_proxy(self, pool: ProxyPool, proxy: ProxyEndpoint) -> None:
        db = await self._get_db()
        await db.execute(
            """
            INSERT INTO proxies (id, pool, score, scheme, anonymity, source, country, payload)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                pool = excluded.pool,
                score = excluded.score,
                scheme = excluded.scheme,
                anonymity = excluded.anonymity,
                source = excluded.source,
                country = excluded.country,
                payload = excluded.payload
            """,
            (
                proxy.id,
                pool,
                proxy.score,
                proxy.scheme,
                proxy.anonymity,
                proxy.source,
                proxy.country,
                serialize_proxy(proxy),
            ),
        )
        await db.commit()

    # Keep interface compatible with code that calls from_url
    @classmethod
    def from_url(cls, redis_url: str, **kwargs: object) -> SQLiteStore:
        """Compatibility shim — ignores the redis_url and creates a SQLite store."""
        return cls.from_path()
