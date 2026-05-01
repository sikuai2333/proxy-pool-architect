from typing import Literal

from pydantic import BaseModel, Field

AuthMethod = Literal["session", "basic", "disabled"]


class AuthLoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=128)
    password: str = Field(min_length=1, max_length=512)


class AuthSession(BaseModel):
    username: str
    created_at: str
    expires_at: str


class AuthStatusResponse(BaseModel):
    enabled: bool
    authenticated: bool
    username: str | None = None
    expires_at: str | None = None
    auth_method: AuthMethod | None = None

