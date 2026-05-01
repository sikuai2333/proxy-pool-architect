from typing import Literal

from pydantic import AnyHttpUrl, BaseModel, Field

ProxyListFileType = Literal["auto", "http", "socks5", "all", "clash", "v2ray"]
SubscriptionDetectedFormat = Literal[
    "plain_text",
    "clash_yaml",
    "v2ray_uri_list",
    "base64_uri_list",
]
ConnectionSupportMode = Literal["direct", "core_adapter"]


class ProxyUrlImportRequest(BaseModel):
    url: AnyHttpUrl
    file_type: ProxyListFileType = "auto"


class ProxyUrlImportResponse(BaseModel):
    source: str
    file_type: ProxyListFileType
    detected_format: SubscriptionDetectedFormat = "plain_text"
    fetched_count: int = Field(default=0, ge=0)
    valid_count: int = Field(default=0, ge=0)
    stored_count: int = Field(default=0, ge=0)
    duplicate_count: int = Field(default=0, ge=0)
    invalid_count: int = Field(default=0, ge=0)
    direct_supported_count: int = Field(default=0, ge=0)
    adapter_required_count: int = Field(default=0, ge=0)
    unsupported_count: int = Field(default=0, ge=0)
    detected_protocols: list[str] = Field(default_factory=list)
    supported_connection_modes: list[ConnectionSupportMode] = Field(default_factory=list)
