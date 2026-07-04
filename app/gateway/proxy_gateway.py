"""Local HTTP CONNECT proxy gateway.

Listens on a configurable port and forwards traffic through proxies
from the pool. Supports per-connection routing via custom headers:

  X-Proxy-Country: US
  X-Proxy-Scheme: socks5
  X-Proxy-Strategy: best | random | rotate

Usage:
  requests.get("http://httpbin.org/ip", proxies={
      "http": "http://127.0.0.1:7890",
      "https": "http://127.0.0.1:7890",
  })
"""

from __future__ import annotations

import asyncio
import contextlib
import random

from loguru import logger

from app.models.proxy import ProxyEndpoint, ProxyFilters
from app.storage.sqlite_store import SQLiteStore

_PROXY_CONNECT_TIMEOUT = 10
_RELAY_BUF_SIZE = 65536


class ProxyGateway:
    def __init__(
        self,
        store: SQLiteStore,
        host: str = "127.0.0.1",
        port: int = 7890,
        default_country: str | None = None,
        default_scheme: str | None = None,
        default_strategy: str = "best",
    ) -> None:
        self._store = store
        self._host = host
        self._port = port
        self._default_country = default_country
        self._default_scheme = default_scheme
        self._default_strategy = default_strategy
        self._server: asyncio.Server | None = None
        self._rotate_index = 0

    @property
    def running(self) -> bool:
        return self._server is not None and self._server.is_serving()

    async def start(self) -> None:
        self._server = await asyncio.start_server(
            self._handle_client, self._host, self._port
        )
        logger.info("Proxy gateway started on {}:{}", self._host, self._port)

    async def stop(self) -> None:
        if self._server is not None:
            self._server.close()
            await self._server.wait_closed()
            self._server = None
            logger.info("Proxy gateway stopped")

    async def _handle_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        try:
            request_line = await asyncio.wait_for(reader.readline(), timeout=30)
            line = request_line.decode("utf-8", errors="replace").strip()
            if not line:
                writer.close()
                return

            parts = line.split()
            if len(parts) < 3 or parts[0].upper() != "CONNECT":
                writer.write(b"HTTP/1.1 405 Method Not Allowed\r\n\r\n")
                await writer.drain()
                writer.close()
                return

            target = parts[1]
            if ":" in target:
                host, port_str = target.rsplit(":", 1)
                try:
                    port = int(port_str)
                except ValueError:
                    writer.write(b"HTTP/1.1 400 Bad Request\r\n\r\n")
                    await writer.drain()
                    writer.close()
                    return
            else:
                host = target
                port = 443

            # Read headers for per-connection config
            country = self._default_country
            scheme = self._default_scheme
            strategy = self._default_strategy

            while True:
                header_line = await asyncio.wait_for(reader.readline(), timeout=10)
                if header_line in (b"\r\n", b"\n", b""):
                    break
                header = header_line.decode("utf-8", errors="replace").strip()
                low = header.lower()
                if low.startswith("x-proxy-country:"):
                    country = header.split(":", 1)[1].strip() or None
                elif low.startswith("x-proxy-scheme:"):
                    scheme = header.split(":", 1)[1].strip() or None
                elif low.startswith("x-proxy-strategy:"):
                    strategy = header.split(":", 1)[1].strip() or self._default_strategy

            proxy = await self._select_proxy(country, scheme, strategy)
            if proxy is None:
                writer.write(
                    b"HTTP/1.1 503 Service Unavailable\r\n"
                    b"X-Proxy-Error: no-suitable-proxy\r\n\r\n"
                )
                await writer.drain()
                writer.close()
                return

            logger.debug(
                "Gateway CONNECT {}:{} via {} ({}:{})",
                host, port, proxy.id, proxy.host, proxy.port,
            )

            upstream_r, upstream_w = await self._connect_through_proxy(proxy, host, port)
            if upstream_r is None or upstream_w is None:
                writer.write(
                    b"HTTP/1.1 502 Bad Gateway\r\n"
                    b"X-Proxy-Error: upstream-connect-failed\r\n\r\n"
                )
                await writer.drain()
                writer.close()
                return

            writer.write(b"HTTP/1.1 200 Connection Established\r\n\r\n")
            await writer.drain()

            await asyncio.gather(
                _pipe(reader, upstream_w, "client->upstream"),
                _pipe(upstream_r, writer, "upstream->client"),
                return_exceptions=True,
            )
        except (TimeoutError, ConnectionError, OSError):
            pass
        except Exception as exc:
            logger.debug("Gateway client handler error: {}", exc)
        finally:
            with contextlib.suppress(Exception):
                writer.close()

    async def _select_proxy(
        self,
        country: str | None,
        scheme: str | None,
        strategy: str,
    ) -> ProxyEndpoint | None:
        filters = ProxyFilters(
            country=country,
            scheme=scheme,  # type: ignore[arg-type]
        )

        if strategy == "random":
            proxies, _ = await self._store.list_filtered_proxies(
                pool=None, filters=filters, limit=50, offset=0
            )
            return random.choice(proxies) if proxies else None

        if strategy == "rotate":
            proxies, _ = await self._store.list_filtered_proxies(
                pool=None, filters=filters, limit=50, offset=0
            )
            if proxies:
                proxy = proxies[self._rotate_index % len(proxies)]
                self._rotate_index += 1
                return proxy
            return None

        # Default: "best" — highest score
        return await self._store.get_best_proxy(filters)

    async def _connect_through_proxy(
        self,
        proxy: ProxyEndpoint,
        target_host: str,
        target_port: int,
    ) -> tuple[asyncio.StreamReader | None, asyncio.StreamWriter | None]:
        try:
            upstream_r, upstream_w = await asyncio.wait_for(
                asyncio.open_connection(proxy.host, proxy.port),
                timeout=_PROXY_CONNECT_TIMEOUT,
            )
        except (TimeoutError, OSError):
            return None, None

        if proxy.scheme in ("socks5", "socks4"):
            ok = await self._socks_handshake(
                upstream_r, upstream_w, target_host, target_port, proxy.scheme
            )
            if not ok:
                upstream_w.close()
                return None, None
            return upstream_r, upstream_w

        # HTTP proxy — send CONNECT
        req_lines = [
            f"CONNECT {target_host}:{target_port} HTTP/1.1",
            f"Host: {target_host}:{target_port}",
        ]
        if proxy.username and proxy.password:
            import base64

            creds = base64.b64encode(f"{proxy.username}:{proxy.password}".encode()).decode()
            req_lines.append(f"Proxy-Authorization: Basic {creds}")
        req_lines.append("")
        req_lines.append("")

        upstream_w.write("\r\n".join(req_lines).encode())
        await upstream_w.drain()

        resp_line = await asyncio.wait_for(
            upstream_r.readline(), timeout=_PROXY_CONNECT_TIMEOUT
        )
        status = resp_line.decode("utf-8", errors="replace").strip()

        # Drain remaining headers
        while True:
            h = await asyncio.wait_for(upstream_r.readline(), timeout=10)
            if h in (b"\r\n", b"\n", b""):
                break

        if "200" in status:
            return upstream_r, upstream_w

        logger.debug("Upstream proxy {} returned: {}", proxy.id, status)
        upstream_w.close()
        return None, None

    async def _socks_handshake(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        target_host: str,
        target_port: int,
        version: str,
    ) -> bool:
        if version == "socks5":
            # Greeting: no auth
            writer.write(b"\x05\x01\x00")
            await writer.drain()
            resp = await asyncio.wait_for(reader.read(2), timeout=_PROXY_CONNECT_TIMEOUT)
            if len(resp) < 2 or resp[0] != 0x05:
                return False

            # CONNECT request
            host_bytes = target_host.encode("ascii")
            req = bytearray([0x05, 0x01, 0x00, 0x03, len(host_bytes)])
            req.extend(host_bytes)
            req.extend(target_port.to_bytes(2, "big"))
            writer.write(bytes(req))
            await writer.drain()

            resp = await asyncio.wait_for(reader.read(10), timeout=_PROXY_CONNECT_TIMEOUT)
            return len(resp) >= 2 and resp[1] == 0x00

        # SOCKS4 / SOCKS4a
        if version == "socks4":
            import socket

            try:
                addr = socket.inet_aton(target_host)
                req = bytearray([0x04, 0x01])
                req.extend(target_port.to_bytes(2, "big"))
                req.extend(addr)
                req.append(0x00)
            except OSError:
                # SOCKS4a
                addr = b"\x00\x00\x00\x01"
                req = bytearray([0x04, 0x01])
                req.extend(target_port.to_bytes(2, "big"))
                req.extend(addr)
                req.append(0x00)
                req.extend(target_host.encode("ascii"))
                req.append(0x00)
            writer.write(bytes(req))
            await writer.drain()
            resp = await asyncio.wait_for(reader.read(8), timeout=_PROXY_CONNECT_TIMEOUT)
            return len(resp) >= 2 and resp[1] == 0x5A

        return False


async def _pipe(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
    _label: str,
) -> None:
    try:
        while True:
            data = await reader.read(_RELAY_BUF_SIZE)
            if not data:
                break
            writer.write(data)
            await writer.drain()
    except (TimeoutError, ConnectionError, OSError):
        pass
    finally:
        with contextlib.suppress(Exception):
            if writer.can_write_eof():
                writer.write_eof()
        with contextlib.suppress(Exception):
            writer.close()
