from __future__ import annotations

import hmac
import secrets
from typing import Literal

from fastapi.security import HTTPBasicCredentials

from app.core.config import Settings
from app.models.auth import AuthMethod, AuthSession, AuthStatusResponse
from app.storage.redis_store import RedisStore
from app.utils.time import utc_now_iso, utc_plus_seconds_iso


class AuthenticatedAdmin(AuthSession):
    auth_method: AuthMethod


class AuthService:
    def __init__(self, store: RedisStore, settings: Settings) -> None:
        self._store = store
        self._settings = settings

    @property
    def enabled(self) -> bool:
        return self._settings.auth_enabled

    @property
    def cookie_name(self) -> str:
        return self._settings.auth_session_cookie_name

    @property
    def session_ttl_seconds(self) -> int:
        return self._settings.auth_session_ttl_seconds

    @property
    def cookie_secure(self) -> bool:
        return self._settings.auth_session_secure

    @property
    def cookie_samesite(self) -> Literal["lax", "strict", "none"]:
        return self._settings.auth_session_samesite

    def verify_admin_credentials(self, username: str, password: str) -> bool:
        expected_username = self._settings.auth_admin_username
        expected_password = self._settings.auth_admin_password
        if not self.enabled or not expected_username or not expected_password:
            return False
        return hmac.compare_digest(username, expected_username) and hmac.compare_digest(
            password, expected_password
        )

    async def create_session(self, username: str) -> tuple[str, AuthSession]:
        token = secrets.token_urlsafe(32)
        session = AuthSession(
            username=username,
            created_at=utc_now_iso(),
            expires_at=utc_plus_seconds_iso(self.session_ttl_seconds),
        )
        await self._store.save_admin_session(
            token,
            session.model_dump_json(),
            self.session_ttl_seconds,
        )
        return token, session

    async def get_session(self, token: str | None) -> AuthSession | None:
        if not token:
            return None
        payload = await self._store.get_admin_session(token)
        if payload is None:
            return None
        try:
            return AuthSession.model_validate_json(payload)
        except ValueError:
            await self._store.delete_admin_session(token)
            return None

    async def delete_session(self, token: str | None) -> None:
        if token:
            await self._store.delete_admin_session(token)

    async def authenticate(
        self,
        *,
        cookie_token: str | None,
        credentials: HTTPBasicCredentials | None,
    ) -> AuthenticatedAdmin | None:
        if not self.enabled:
            return None

        session = await self.get_session(cookie_token)
        if session is not None:
            return AuthenticatedAdmin(
                username=session.username,
                created_at=session.created_at,
                expires_at=session.expires_at,
                auth_method="session",
            )

        if credentials and self.verify_admin_credentials(
            credentials.username,
            credentials.password,
        ):
            return AuthenticatedAdmin(
                username=credentials.username,
                created_at=utc_now_iso(),
                expires_at=utc_plus_seconds_iso(self.session_ttl_seconds),
                auth_method="basic",
            )

        return None

    async def build_status(
        self,
        *,
        cookie_token: str | None,
        credentials: HTTPBasicCredentials | None,
    ) -> AuthStatusResponse:
        if not self.enabled:
            return AuthStatusResponse(
                enabled=False,
                authenticated=False,
                auth_method="disabled",
            )

        authenticated = await self.authenticate(
            cookie_token=cookie_token,
            credentials=credentials,
        )
        if authenticated is None:
            return AuthStatusResponse(enabled=True, authenticated=False)

        return AuthStatusResponse(
            enabled=True,
            authenticated=True,
            username=authenticated.username,
            expires_at=authenticated.expires_at,
            auth_method=authenticated.auth_method,
        )
