from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import HTTPBasicCredentials

from app.api.auth import basic_security, get_auth_service
from app.models.auth import AuthLoginRequest, AuthStatusResponse
from app.services.auth_service import AuthService

router = APIRouter(tags=["auth"])


@router.get("/auth/session", response_model=AuthStatusResponse)
async def get_auth_session(
    request: Request,
    service: Annotated[AuthService, Depends(get_auth_service)],
    credentials: Annotated[HTTPBasicCredentials | None, Depends(basic_security)],
) -> AuthStatusResponse:
    return await service.build_status(
        cookie_token=request.cookies.get(service.cookie_name),
        credentials=credentials,
    )


@router.post("/auth/login", response_model=AuthStatusResponse)
async def login(
    payload: AuthLoginRequest,
    response: Response,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> AuthStatusResponse:
    if not service.enabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="auth is disabled")
    if not service.verify_admin_credentials(payload.username, payload.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid credentials",
            headers={"WWW-Authenticate": 'Basic realm="ProxyPool Architect"'},
        )

    token, session = await service.create_session(payload.username)
    response.set_cookie(
        key=service.cookie_name,
        value=token,
        httponly=True,
        secure=service.cookie_secure,
        samesite=service.cookie_samesite,
        max_age=service.session_ttl_seconds,
        path="/",
    )
    return AuthStatusResponse(
        enabled=True,
        authenticated=True,
        username=session.username,
        expires_at=session.expires_at,
        auth_method="session",
    )


@router.post("/auth/logout", response_model=AuthStatusResponse)
async def logout(
    request: Request,
    response: Response,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> AuthStatusResponse:
    await service.delete_session(request.cookies.get(service.cookie_name))
    response.delete_cookie(service.cookie_name, path="/")
    return AuthStatusResponse(enabled=service.enabled, authenticated=False)
