from typing import cast

from fastapi import Request

from app.storage.redis_store import RedisStore


def get_store(request: Request) -> RedisStore:
    return cast(RedisStore, request.app.state.store)
