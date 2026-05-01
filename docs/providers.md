# Provider Configuration

Provider configuration can be supplied with `config/providers.yaml`. The file is ignored by Git
because it may contain subscription URLs or proxy credentials. Start from
`config/providers.yaml.example`.

## Built-In Provider Types

### static

```yaml
providers:
  - type: static
    enabled: true
    options:
      proxies:
        - "http://127.0.0.1:8080"
```

### url_list

```yaml
providers:
  - type: url_list
    enabled: true
    options:
      urls:
        - "https://example.com/proxies.txt"
      timeout_seconds: 10
      concurrency: 5
```

Configured URL lists can contain full proxy URLs such as `http://1.2.3.4:8080` or bare
`host:port` entries. Bare entries default to `http://` when the provider cannot infer a scheme.

### clash_subscription

Parses Clash/FlClash style YAML subscriptions, V2Ray/Xray URI lists, and plain text
HTTP/SOCKS URL lists. Direct HTTP/SOCKS entries are converted into pool proxies. Advanced node
types such as `vmess`, `vless`, `trojan`, `ss`, `hysteria2`, and `tuic` are recognized and
classified as requiring a local core adapter before they can be used as pool endpoints.

```yaml
providers:
  - type: clash_subscription
    enabled: true
    options:
      files:
        - "config/clash-subscription.yaml"
      urls: []
      timeout_seconds: 10
      concurrency: 3
```

### tor

Registers a local Tor SOCKS endpoint. This assumes Tor is already running locally. The provider
does not control Tor, rotate identities, or fetch remote exit lists.

```yaml
providers:
  - type: tor
    enabled: true
    options:
      socks_host: "127.0.0.1"
      socks_port: 9050
```

### core_adapter

Starts or connects to a local adapter core such as Clash, FlClash, Mihomo, Xray/V2Ray, or
sing-box. The core is responsible for VMess, VLESS, Trojan, Shadowsocks, Hysteria, TUIC,
WireGuard, and similar node protocols. ProxyPool Architect only consumes the local HTTP/SOCKS
inbound exposed by that core.

```yaml
providers:
  - type: core_adapter
    enabled: true
    options:
      core_name: "mihomo"
      command: ["mihomo", "-f", "config/mihomo.yaml"]
      config_file: "config/mihomo.yaml"
      local_host: "127.0.0.1"
      local_scheme: "http"
      local_port: 7890
      readiness_url: "http://127.0.0.1:9090/version"
      startup_timeout_seconds: 10
      shutdown_on_exit: true
```

If `local_scheme` and `local_port` are omitted, the provider tries to infer the inbound from the
core config using Clash-style `mixed-port`, `socks-port`, and `port`, then falls back to
`inbounds` entries from Xray/V2Ray or sing-box style configs. Readiness checks are limited to
local URLs such as `127.0.0.1` or `localhost`.

If the core is managed outside this application, omit `command` and configure only the local
inbound:

```yaml
providers:
  - type: core_adapter
    enabled: true
    options:
      core_name: "external-mihomo"
      local_scheme: "socks5"
      local_host: "127.0.0.1"
      local_port: 7891
```

## Dashboard URL Import

The React dashboard Providers page can submit an on-demand source URL to:

```text
POST /providers/import-url
```

Request body:

```json
{
  "url": "https://example.com/http.txt",
  "file_type": "http"
}
```

Supported `file_type` values:

- `auto`: auto-detect plain text, Clash/FlClash YAML, and V2Ray/Xray subscription payloads
- `http`: bare `host:port` entries are normalized to `http://host:port`
- `socks5`: bare `host:port` entries are normalized to `socks5://host:port`
- `all`: mixed lists can include `http://`, `https://`, `socks4://`, or `socks5://` entries
- `clash`: force Clash/FlClash YAML parsing first, then fall back to direct text parsing
- `v2ray`: force V2Ray/Xray URI parsing, including base64-encoded subscription payloads

The endpoint stores unique direct proxies into the `raw` pool and returns detected format,
protocol list, direct-supported count, adapter-required count, unsupported count, duplicate
count, and invalid count. Only `http` and `https` source URLs are accepted. Literal private or
local source hosts are blocked when `SAFE_BLOCK_PRIVATE_NETWORKS=true`.

## Custom Providers

Custom providers can be loaded by class path. Dynamic imports execute trusted application code,
so only class paths matching `PROVIDER_PLUGIN_ALLOWED_PREFIXES` are accepted.

```yaml
providers:
  - type: custom
    enabled: true
    class_path: "app.providers.static_provider.StaticProvider"
    options:
      proxies:
        - "http://127.0.0.1:8080"
```

## Geo Data

Geo enrichment uses a local CSV file with `cidr,country,asn` columns:

```csv
cidr,country,asn
1.2.3.0/24,US,AS64500
```

Enable it with:

```env
GEO_ENABLED=true
GEO_FILE=config/geo.csv
```

The resolver only matches literal IP hosts. It does not perform DNS lookups or call external Geo
APIs.
