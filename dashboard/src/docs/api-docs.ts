export const apiDocZh = `# ProxyPool Architect API 文档

## 基础信息

- **Base URL**: \`http://localhost:8000/api\`
- **认证**: 启用 \`AUTH_ENABLED=true\` 后需要 HTTP Basic Auth 或 Session Cookie
- **Content-Type**: \`application/json\`
- **字符编码**: UTF-8

---

## 代理接口

### 获取单个代理

根据筛选条件返回最优代理。

\`\`\`
GET /api/proxy
\`\`\`

**Query 参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| scheme | string | 否 | 协议: \`http\`, \`https\`, \`socks4\`, \`socks5\` |
| anonymity | string | 否 | 匿名级别: \`unknown\`, \`transparent\`, \`anonymous\`, \`elite\` |
| country | string | 否 | 国家代码，如 \`US\`, \`CN\`, \`SG\` |
| min_score | int | 否 | 最低分数 |
| session_id | string | 否 | 会话 ID（最长 128 字符），用于会话亲和 |
| format | string | 否 | 响应格式: \`json\`（默认）, \`text\` |

**响应示例 (JSON)**

\`\`\`json
{
  "id": "http-1.2.3.4-8080",
  "scheme": "http",
  "host": "1.2.3.4",
  "port": 8080,
  "auth_required": true,
  "source": "static",
  "country": "US",
  "anonymity": "elite",
  "latency_ms": 120,
  "success_count": 5,
  "fail_count": 1,
  "score": 95,
  "status": "elite"
}
\`\`\`

**响应示例 (text)**

\`\`\`
http://1.2.3.4:8080
\`\`\`

> 注意: \`format=text\` 不包含认证信息。

**curl 示例**

\`\`\`bash
curl "http://localhost:8000/api/proxy?scheme=http&country=US&min_score=80"
curl "http://localhost:8000/api/proxy?session_id=my-task-123"
curl "http://localhost:8000/api/proxy?format=text"
\`\`\`

---

### 代理列表

分页查询代理列表，支持多种筛选。

\`\`\`
GET /api/proxy/list
\`\`\`

**Query 参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pool | string | 否 | 池名: \`raw\`, \`checked\`, \`elite\`, \`dead\`, \`cooldown\` |
| scheme | string | 否 | 协议 |
| anonymity | string | 否 | 匿名级别 |
| country | string | 否 | 国家代码 |
| source | string | 否 | 来源名称 |
| q | string | 否 | 主机名或 ID 子串搜索 |
| min_score | int | 否 | 最低分数 |
| limit | int | 否 | 每页数量 (1-500, 默认 100) |
| offset | int | 否 | 偏移量 (默认 0) |

**响应示例**

\`\`\`json
{
  "items": [...],
  "total": 42,
  "proxies": [...],
  "count": 20,
  "limit": 20,
  "offset": 0
}
\`\`\`

**curl 示例**

\`\`\`bash
curl "http://localhost:8000/api/proxy/list?pool=elite&limit=20&offset=0"
curl "http://localhost:8000/api/proxy/list?source=static&country=US"
\`\`\`

---

### 代理详情

根据代理 ID 获取详细信息。

\`\`\`
GET /api/proxy/{proxy_id}
\`\`\`

**路径参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| proxy_id | string | 代理 ID，如 \`http-1.2.3.4-8080\` |

**curl 示例**

\`\`\`bash
curl "http://localhost:8000/api/proxy/http-1.2.3.4-8080"
\`\`\`

---

### 上报使用结果

向系统反馈代理使用结果，影响评分和池分配。

\`\`\`
POST /api/proxy/report
\`\`\`

**请求体**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| proxy_id | string | 是 | 代理 ID |
| ok | bool | 是 | 是否成功 |
| latency_ms | int | 否 | 延迟 (毫秒) |
| error | string | 否 | 错误描述 |

**响应示例**

\`\`\`json
{
  "proxy_id": "http-1.2.3.4-8080",
  "status": "checked",
  "score": 60,
  "success_count": 3,
  "fail_count": 1
}
\`\`\`

**curl 示例**

\`\`\`bash
curl -X POST "http://localhost:8000/api/proxy/report" \\
  -H "Content-Type: application/json" \\
  -d '{"proxy_id":"http-1.2.3.4-8080","ok":true,"latency_ms":80}'
\`\`\`

---

### 删除代理

\`\`\`
DELETE /api/proxy/{proxy_id}
\`\`\`

**curl 示例**

\`\`\`bash
curl -X DELETE "http://localhost:8000/api/proxy/http-1.2.3.4-8080"
\`\`\`

---

## 统计接口

### 获取统计信息

\`\`\`
GET /api/stats
\`\`\`

**响应字段**

| 字段 | 类型 | 说明 |
|------|------|------|
| pools | object | 各池代理数量 |
| total | int | 代理总数 |
| average_latency_ms | float | 平均延迟 (ms) |
| success_rate | float | 成功率 (0-1) |
| db_status | string | 数据库状态 |
| scheduler_status | string | 调度器状态 |

**curl 示例**

\`\`\`bash
curl "http://localhost:8000/api/stats"
\`\`\`

---

## 健康检查

\`\`\`
GET /api/health
\`\`\`

**响应示例**

\`\`\`json
{
  "status": "ok",
  "app": "ProxyPool Architect",
  "version": "0.1.0",
  "environment": "dev",
  "db_configured": true,
  "db": "ok",
  "scheduler": "stopped"
}
\`\`\`

---

## 来源管理

### 来源列表

\`\`\`
GET /api/providers
\`\`\`

### 来源详情

\`\`\`
GET /api/providers/{provider_name}
\`\`\`

### 导入代理 URL

从远程 URL 导入代理列表。

\`\`\`
POST /api/providers/import-url
\`\`\`

**请求体**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| url | string | 是 | 代理列表 URL |
| file_type | string | 是 | 类型: \`auto\`, \`http\`, \`socks5\`, \`all\`, \`clash\`, \`v2ray\` |

**curl 示例**

\`\`\`bash
curl -X POST "http://localhost:8000/api/providers/import-url" \\
  -H "Content-Type: application/json" \\
  -d '{"url":"https://example.com/http.txt","file_type":"auto"}'
\`\`\`

---

## 地理信息

\`\`\`
GET /api/geo/summary
\`\`\`

返回代理的国家分布、ASN 分布和覆盖率信息。

---

## 验证任务

### 验证任务列表

\`\`\`
GET /api/validation/jobs?limit=50&offset=0
\`\`\`

### 手动触发验证

\`\`\`
POST /api/validation/run?limit=100
\`\`\`

---

## 事件日志

\`\`\`
GET /api/events?limit=50&offset=0
\`\`\`

---

## 运行时设置

### 获取设置

\`\`\`
GET /api/settings
\`\`\`

### 更新设置

\`\`\`
PATCH /api/settings
\`\`\`

**请求体示例**

\`\`\`json
{
  "fetch_interval_seconds": 900,
  "validate_interval_seconds": 300,
  "validate_timeout_seconds": 5,
  "validate_concurrency": 50,
  "min_elite_score": 85,
  "cooldown_seconds": 1200,
  "safe_networking": {
    "authorized_targets_only": true,
    "block_private_networks": true,
    "mask_proxy_credentials": true
  }
}
\`\`\`

---

## 认证接口

### 检查会话状态

\`\`\`
GET /api/auth/session
\`\`\`

### 登录

\`\`\`
POST /api/auth/login
\`\`\`

**请求体**

\`\`\`json
{"username": "admin", "password": "your-password"}
\`\`\`

### 登出

\`\`\`
POST /api/auth/logout
\`\`\`

---

## 监控接口

### Prometheus 指标

\`\`\`
GET /api/metrics
\`\`\`

返回 Prometheus 兼容的文本格式指标。

---

## 本地代理网关

启用 \`GATEWAY_ENABLED=true\` 后，应用会在 \`GATEWAY_PORT\`（默认 7890）启动一个 HTTP CONNECT 代理网关。

### Python 使用示例

\`\`\`python
import requests

# 自动选择最优代理
requests.get("http://httpbin.org/ip", proxies={
    "http": "http://127.0.0.1:7890",
    "https": "http://127.0.0.1:7890",
})
\`\`\`

### 自定义请求头

每个连接可通过自定义请求头指定路由规则:

| 请求头 | 说明 | 示例 |
|--------|------|------|
| X-Proxy-Country | 按国家筛选 | \`US\`, \`CN\`, \`SG\` |
| X-Proxy-Scheme | 按协议筛选 | \`socks5\`, \`http\` |
| X-Proxy-Strategy | 选择策略 | \`best\`, \`random\`, \`rotate\` |

### 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| GATEWAY_ENABLED | false | 是否启用网关 |
| GATEWAY_PORT | 7890 | 监听端口 |
| GATEWAY_HOST | 127.0.0.1 | 监听地址 |
| GATEWAY_DEFAULT_COUNTRY | (空) | 默认国家筛选 |
| GATEWAY_DEFAULT_SCHEME | (空) | 默认协议筛选 |
| GATEWAY_DEFAULT_STRATEGY | best | 默认选择策略 |

---

## GitHub 镜像加速

当从 GitHub（raw.githubusercontent.com、github.com）抓取代理列表时，系统会自动尝试多个镜像站，提高在国内网络环境下的成功率。

### 配置方式

在 \`.env\` 中设置 \`GITHUB_MIRRORS\`（JSON 数组或逗号分隔）:

\`\`\`
GITHUB_MIRRORS=["https://gh-proxy.com/","https://ghproxy.net/","https://ghproxy.homeboyc.cn/","https://github.akams.cn/"]
\`\`\`

### 工作原理

1. 系统首先尝试原始 GitHub URL
2. 如果失败，依次尝试每个镜像站
3. 镜像 URL 格式: \`{镜像站地址}/{原始 GitHub URL}\`
4. 对非 GitHub URL 不做处理

### 支持的 URL 格式

- \`raw.githubusercontent.com\` — Raw 文件内容
- \`github.com\` — Release 下载、仓库归档
`;

export const apiDocEn = `# ProxyPool Architect API Reference

## Base Info

- **Base URL**: \`http://localhost:8000/api\`
- **Auth**: HTTP Basic Auth or session cookie when \`AUTH_ENABLED=true\`
- **Content-Type**: \`application/json\`
- **Encoding**: UTF-8

---

## Proxy Endpoints

### Get Proxy

Returns the best proxy matching the given filters.

\`\`\`
GET /api/proxy
\`\`\`

**Query Parameters**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| scheme | string | No | Protocol: \`http\`, \`https\`, \`socks4\`, \`socks5\` |
| anonymity | string | No | Level: \`unknown\`, \`transparent\`, \`anonymous\`, \`elite\` |
| country | string | No | Country code, e.g. \`US\`, \`CN\` |
| min_score | int | No | Minimum score |
| session_id | string | No | Session ID (max 128 chars) for affinity |
| format | string | No | Response: \`json\` (default) or \`text\` |

**Example**

\`\`\`bash
curl "http://localhost:8000/api/proxy?scheme=http&country=US"
\`\`\`

---

### List Proxies

Paginated proxy list with filters.

\`\`\`
GET /api/proxy/list
\`\`\`

**Query Parameters**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| pool | string | No | Pool: \`raw\`, \`checked\`, \`elite\`, \`dead\`, \`cooldown\` |
| scheme | string | No | Protocol |
| anonymity | string | No | Anonymity level |
| country | string | No | Country code |
| source | string | No | Provider source name |
| q | string | No | Host/ID substring search |
| min_score | int | No | Minimum score |
| limit | int | No | Page size (1-500, default 100) |
| offset | int | No | Offset (default 0) |

---

### Proxy Detail

\`\`\`
GET /api/proxy/{proxy_id}
\`\`\`

---

### Report Result

\`\`\`
POST /api/proxy/report
\`\`\`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| proxy_id | string | Yes | Proxy ID |
| ok | bool | Yes | Success or not |
| latency_ms | int | No | Latency in ms |
| error | string | No | Error message |

---

### Delete Proxy

\`\`\`
DELETE /api/proxy/{proxy_id}
\`\`\`

---

## Stats

\`\`\`
GET /api/stats
\`\`\`

---

## Health

\`\`\`
GET /api/health
\`\`\`

---

## Providers

\`\`\`
GET  /api/providers
GET  /api/providers/{name}
POST /api/providers/import-url
\`\`\`

---

## Geo

\`\`\`
GET /api/geo/summary
\`\`\`

---

## Validation Jobs

\`\`\`
GET  /api/validation/jobs?limit=50&offset=0
POST /api/validation/run?limit=100
\`\`\`

---

## Events

\`\`\`
GET /api/events?limit=50&offset=0
\`\`\`

---

## Settings

\`\`\`
GET   /api/settings
PATCH /api/settings
\`\`\`

---

## Auth

\`\`\`
GET  /api/auth/session
POST /api/auth/login
POST /api/auth/logout
\`\`\`

---

## Metrics

\`\`\`
GET /api/metrics
\`\`\`

Prometheus-compatible text format.

---

## Proxy Gateway

Enable with \`GATEWAY_ENABLED=true\`. Default port: 7890.

\`\`\`python
import requests

requests.get("http://httpbin.org/ip", proxies={
    "http": "http://127.0.0.1:7890",
    "https": "http://127.0.0.1:7890",
})
\`\`\`

**Custom Headers**

| Header | Description | Example |
|--------|-------------|---------|
| X-Proxy-Country | Filter by country | \`US\` |
| X-Proxy-Scheme | Filter by protocol | \`socks5\` |
| X-Proxy-Strategy | Selection strategy | \`best\`, \`random\`, \`rotate\` |
`;
