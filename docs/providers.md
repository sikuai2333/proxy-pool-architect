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

### clash_subscription

Parses Clash/FlClash style YAML subscriptions and plain text HTTP/SOCKS URL lists. Supported
Clash node types are `http`, `socks4`, and `socks5`. Unsupported types such as `vmess`,
`trojan`, and `ss` are skipped because they are not simple HTTP/SOCKS proxy endpoints.

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
