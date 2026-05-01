import asyncio
import atexit
import subprocess
import sys
from pathlib import Path
from time import monotonic
from urllib.parse import urlparse

import httpx
import yaml
from loguru import logger

from app.models.proxy import ProxyEndpoint, ProxyScheme
from app.providers.base import ProxyProvider
from app.utils.proxy_url import build_proxy_id

_PROCESS_REGISTRY: dict[str, subprocess.Popen[bytes]] = {}
_CLEANUP_REGISTERED = False
_LOCAL_READINESS_HOSTS = {"127.0.0.1", "localhost", "::1"}


class CoreAdapterProvider(ProxyProvider):
    name = "core_adapter"

    def __init__(
        self,
        core_name: str = "core",
        enabled: bool = True,
        command: list[str] | None = None,
        working_dir: str | None = None,
        config_file: str | None = None,
        local_scheme: ProxyScheme | None = None,
        local_host: str = "127.0.0.1",
        local_port: int | None = None,
        readiness_url: str | None = None,
        startup_timeout_seconds: float = 10.0,
        shutdown_on_exit: bool = True,
    ) -> None:
        self._core_name = core_name
        self.name = f"core_adapter:{core_name}"
        self.enabled = enabled
        self._command = command or []
        self._working_dir = working_dir
        self._config_file = config_file
        self._local_scheme = local_scheme
        self._local_host = local_host
        self._local_port = local_port
        self._readiness_url = readiness_url
        self._startup_timeout_seconds = startup_timeout_seconds
        self._shutdown_on_exit = shutdown_on_exit

    async def fetch(self) -> list[ProxyEndpoint]:
        if not self.enabled:
            return []

        if self._command:
            try:
                self._ensure_started()
            except OSError as exc:
                logger.warning(
                    "Failed to start core adapter {}: {}",
                    self._core_name,
                    exc,
                )
                return []
            ready = await self._wait_until_ready()
            if not ready:
                logger.warning("Core adapter {} did not become ready in time", self._core_name)
                return []

        endpoint = self._resolve_local_endpoint()
        if endpoint is None:
            logger.warning("Core adapter {} has no configured local inbound", self._core_name)
            return []

        scheme, host, port = endpoint
        return [
            ProxyEndpoint(
                id=build_proxy_id(scheme, host, port),
                scheme=scheme,
                host=host,
                port=port,
                source=self.name,
            )
        ]

    def _ensure_started(self) -> None:
        process = _PROCESS_REGISTRY.get(self._core_name)
        if process is not None and process.poll() is None:
            return

        _register_cleanup()
        creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        process = subprocess.Popen(
            self._command,
            cwd=self._working_dir,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            shell=False,
            creationflags=creationflags,
        )
        _PROCESS_REGISTRY[self._core_name] = process
        if self._shutdown_on_exit:
            logger.info("Started core adapter {}", self._core_name)

    async def _wait_until_ready(self) -> bool:
        if self._readiness_url is None:
            return True
        if not _is_local_readiness_url(self._readiness_url):
            logger.warning("Skipping non-local readiness URL for core adapter {}", self._core_name)
            return True

        deadline = monotonic() + self._startup_timeout_seconds
        async with httpx.AsyncClient(timeout=1.0, follow_redirects=False) as client:
            while monotonic() < deadline:
                try:
                    response = await client.get(self._readiness_url)
                except httpx.HTTPError:
                    await asyncio.sleep(0.1)
                    continue
                if response.status_code < 500:
                    return True
                await asyncio.sleep(0.1)
        return False

    def _resolve_local_endpoint(self) -> tuple[ProxyScheme, str, int] | None:
        if self._local_scheme is not None and self._local_port is not None:
            return self._local_scheme, self._local_host, self._local_port

        inferred = self._infer_endpoint_from_config()
        if inferred is not None:
            return inferred

        if self._local_port is not None:
            return "http", self._local_host, self._local_port
        return None

    def _infer_endpoint_from_config(self) -> tuple[ProxyScheme, str, int] | None:
        if self._config_file is None:
            return None
        path = Path(self._config_file)
        if not path.exists():
            return None

        try:
            payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError as exc:
            logger.warning("Failed to parse core adapter config {}: {}", path, exc)
            return None
        if not isinstance(payload, dict):
            return None

        mixed_port = _int_or_none(payload.get("mixed-port"))
        if mixed_port is not None:
            return "http", self._local_host, mixed_port

        socks_port = _int_or_none(payload.get("socks-port"))
        if socks_port is not None:
            return "socks5", self._local_host, socks_port

        http_port = _int_or_none(payload.get("port"))
        if http_port is not None:
            return "http", self._local_host, http_port

        return None


def _register_cleanup() -> None:
    global _CLEANUP_REGISTERED
    if _CLEANUP_REGISTERED:
        return
    atexit.register(_shutdown_started_processes)
    _CLEANUP_REGISTERED = True


def _shutdown_started_processes() -> None:
    for process in _PROCESS_REGISTRY.values():
        if process.poll() is None:
            process.terminate()


def _is_local_readiness_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.hostname in _LOCAL_READINESS_HOSTS


def _int_or_none(value: object) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if not isinstance(value, str | bytes | bytearray):
        return None
    try:
        return int(value)
    except ValueError:
        return None
