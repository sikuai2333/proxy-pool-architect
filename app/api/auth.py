from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from app.api.dependencies import get_store
from app.core.config import get_settings
from app.services.auth_service import AuthenticatedAdmin, AuthService
from app.storage.sqlite_store import SQLiteStore

basic_security = HTTPBasic(auto_error=False)


def get_auth_service(
    store: Annotated[SQLiteStore, Depends(get_store)],
) -> AuthService:
    return AuthService(store=store, settings=get_settings())


def _unauthorized_exception() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="authentication required",
        headers={"WWW-Authenticate": 'Basic realm="ProxyPool Architect"'},
    )


async def require_admin_auth(
    request: Request,
    service: Annotated[AuthService, Depends(get_auth_service)],
    credentials: Annotated[HTTPBasicCredentials | None, Depends(basic_security)],
) -> AuthenticatedAdmin:
    if not service.enabled:
        return AuthenticatedAdmin(
            username="admin",
            created_at="",
            expires_at="",
            auth_method="disabled",
        )

    authenticated = await service.authenticate(
        cookie_token=request.cookies.get(service.cookie_name),
        credentials=credentials,
    )
    if authenticated is None:
        raise _unauthorized_exception()
    return authenticated

