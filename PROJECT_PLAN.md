# ProxyPool Architect 项目规划文档

## 0. 项目定位

项目名称：ProxyPool Architect

目标：从 0 开发一个现代化代理池系统，支持多来源代理采集、代理可用性检测、匿名性检测、评分淘汰、分层存储、API 获取、Dashboard 管理、Docker 部署，并为后续接入付费代理源、flclash、TorProvider 或自建代理节点预留扩展能力。

建议边界：本项目仅用于自有业务、授权测试、合规爬虫、隐私/网络质量测试。不要实现绕过风控、验证码绕过、批量注册、撞库、攻击或滥用功能。

## 1. 核心功能

MVP 必须完成：

1. 支持代理来源采集。
2. 支持 HTTP / HTTPS / SOCKS4 / SOCKS5 代理格式。
3. 支持代理基础连通性检测。
4. 支持匿名性泄露检测。
5. 支持 Redis 存储。
6. 支持 raw / checked / elite 三层代理池。
7. 支持 FastAPI 提供代理获取接口。
8. 支持 Docker Compose 一键启动。
9. 支持配置化代理源。
10. 支持基础 stats API。

长期目标：

1. 多来源 Provider 插件化。
2. 付费代理 Provider。
3. 自建代理节点 Provider。
4. ASN / 国家 / 协议 / 延迟 / 匿名等级评分。
5. 代理使用反馈 report_result。
6. 熔断和冷却机制。
7. 任务级 session affinity。
8. Web Dashboard。
9. Prometheus / Grafana 指标。
10. 可选接入 flclash / TorProvider，但不是 MVP。

## 2. 技术选型

推荐技术栈：

- Python 3.11+
- FastAPI
- aiohttp 或 httpx
- Redis
- APScheduler
- pydantic-settings
- loguru
- pytest + pytest-asyncio
- ruff + mypy
- Docker + Docker Compose
- 后期可选：Next.js / React Dashboard

## 3. 推荐目录结构

```text
proxy-pool-architect/
├─ app/
│  ├─ main.py
│  ├─ api/
│  │  ├─ routes_proxy.py
│  │  ├─ routes_stats.py
│  │  ├─ routes_admin.py
│  │  └─ routes_health.py
│  ├─ core/
│  │  ├─ config.py
│  │  ├─ logging.py
│  │  ├─ scheduler.py
│  │  └─ errors.py
│  ├─ models/
│  │  ├─ proxy.py
│  │  ├─ score.py
│  │  └─ provider.py
│  ├─ providers/
│  │  ├─ base.py
│  │  ├─ static_provider.py
│  │  ├─ url_list_provider.py
│  │  ├─ freeproxy_provider.py
│  │  └─ paid_provider.py
│  ├─ validators/
│  │  ├─ base.py
│  │  ├─ connectivity.py
│  │  ├─ anonymity.py
│  │  ├─ protocol.py
│  │  └─ geo.py
│  ├─ storage/
│  │  ├─ redis_store.py
│  │  ├─ keys.py
│  │  └─ serializers.py
│  ├─ services/
│  │  ├─ fetch_service.py
│  │  ├─ validate_service.py
│  │  ├─ scoring_service.py
│  │  ├─ proxy_service.py
│  │  └─ stats_service.py
│  └─ utils/
│     ├─ proxy_url.py
│     ├─ network.py
│     └─ time.py
├─ tests/
├─ scripts/
├─ docs/
├─ .codex/
│  ├─ config.toml
│  └─ skills/
├─ AGENTS.md
├─ pyproject.toml
├─ docker-compose.yml
├─ Dockerfile
├─ README.md
└─ PROJECT_PLAN.md
```

## 4. 数据模型

### ProxyEndpoint

```python
from pydantic import BaseModel
from typing import Literal

ProxyScheme = Literal["http", "https", "socks4", "socks5"]

class ProxyEndpoint(BaseModel):
    id: str
    scheme: ProxyScheme
    host: str
    port: int
    username: str | None = None
    password: str | None = None

    source: str
    country: str | None = None
    asn: str | None = None
    anonymity: Literal["unknown", "transparent", "anonymous", "elite"] = "unknown"

    latency_ms: int | None = None
    success_count: int = 0
    fail_count: int = 0
    score: int = 0

    last_checked_at: str | None = None
    last_success_at: str | None = None
    last_error: str | None = None

    status: Literal["raw", "checked", "elite", "dead", "cooldown"] = "raw"
```

### 三层代理池

- raw_pool：新采集到的代理，未验证，不对外提供。
- checked_pool：基础连通性通过，可用于低要求任务。
- elite_pool：通过匿名性检查、HTTPS 检查、稳定性评分的代理，对外优先提供。

### Redis Key 设计

```text
proxy:raw:{proxy_id}
proxy:checked:{proxy_id}
proxy:elite:{proxy_id}
proxy:dead:{proxy_id}
proxy:index:raw
proxy:index:checked
proxy:index:elite
proxy:index:dead
proxy:source:{source_name}
proxy:stats
proxy:cooldown
```

## 5. 核心模块设计

### Provider 插件接口

```python
from abc import ABC, abstractmethod
from app.models.proxy import ProxyEndpoint

class ProxyProvider(ABC):
    name: str

    @abstractmethod
    async def fetch(self) -> list[ProxyEndpoint]:
        """Fetch candidate proxies from this provider."""
```

MVP Provider：

1. StaticProvider：读取本地配置里的固定代理。
2. UrlListProvider：从文本 URL 拉取代理列表。
3. FreeProxyProvider：接入第三方免费代理库或公开源。
4. PaidProvider：预留接口，不在 MVP 强依赖。

### Validator

1. ConnectivityValidator：检查代理是否能连接测试 URL，记录延迟、状态码、错误类型。
2. ProtocolValidator：检查 HTTP / HTTPS / SOCKS4 / SOCKS5 是否真实可用。
3. AnonymityValidator：检查是否暴露原始 IP，检查 Via / X-Forwarded-For / Forwarded 等代理头。
4. StabilityValidator：多轮检测，根据成功率和延迟评分。

注意：匿名性检测用于判断代理是否会泄露客户端信息，不用于规避网站风控或机器人检测。

### ScoringService

建议规则：

```text
初始分：50
连通成功：+10
连通失败：-20
匿名性 elite：+30
匿名性 anonymous：+15
透明代理：-50
延迟 < 500ms：+10
延迟 500-1500ms：+5
延迟 > 5000ms：-15
连续失败 3 次：进入 cooldown
连续失败 5 次：进入 dead
```

## 6. API 设计

### GET /health

返回服务状态。

### GET /proxy

参数：

- scheme: http / https / socks4 / socks5
- anonymity: transparent / anonymous / elite
- country: 国家代码
- min_score: 最低分
- format: json / text

### GET /proxy/list

返回代理列表，支持分页和过滤。

### POST /proxy/report

请求体：

```json
{
  "proxy_id": "socks5-1.2.3.4-1080",
  "ok": true,
  "latency_ms": 930,
  "error": null
}
```

### GET /stats

返回 raw / checked / elite / dead 数量、平均延迟、成功率等。

### DELETE /proxy/{proxy_id}

删除指定代理。

## 7. 配置设计

### .env

```env
APP_ENV=dev
APP_HOST=0.0.0.0
APP_PORT=8000
REDIS_URL=redis://redis:6379/0
FETCH_INTERVAL_SECONDS=1800
VALIDATE_INTERVAL_SECONDS=600
VALIDATE_CONCURRENCY=100
VALIDATE_TIMEOUT_SECONDS=10
TEST_URL=https://httpbin.org/ip
ANONYMITY_TEST_URL=https://httpbin.org/headers
MIN_ELITE_SCORE=80
COOLDOWN_SECONDS=1800
```

### config/providers.yaml

```yaml
providers:
  static:
    enabled: true
    proxies:
      - "http://127.0.0.1:8080"

  url_lists:
    enabled: true
    urls:
      - "https://example.com/proxies.txt"

  freeproxy:
    enabled: false

  paid:
    enabled: false
    endpoint: ""
    token_env: "PAID_PROXY_TOKEN"
```

## 8. 分阶段开发计划

### Phase 0：项目初始化

目标：

1. 初始化 Python 项目。
2. 配置 ruff / mypy / pytest。
3. 配置 FastAPI。
4. 配置 Redis。
5. Docker Compose 能启动。

验收：

```bash
docker compose up -d
curl http://localhost:8000/health
pytest
ruff check .
```

### Phase 1：数据模型 + Redis 存储

目标：

1. ProxyEndpoint 模型。
2. RedisStore。
3. raw / checked / elite / dead 四层存储。
4. 基础单元测试。

### Phase 2：Provider 采集模块

目标：

1. StaticProvider。
2. UrlListProvider。
3. ProviderManager。
4. FetchService。

### Phase 3：Validator 检测模块

目标：

1. ConnectivityValidator。
2. ProtocolValidator。
3. AnonymityValidator。
4. ValidateService 并发检测。

### Phase 4：API 服务

目标：

1. GET /proxy。
2. GET /proxy/list。
3. POST /proxy/report。
4. GET /stats。
5. DELETE /proxy/{id}。

### Phase 5：调度系统

目标：

1. APScheduler 启动采集任务。
2. APScheduler 启动检测任务。
3. 启动时自动恢复。
4. 日志清晰。

### Phase 6：Dashboard

目标：

1. 展示代理数量。
2. 展示 elite / checked / raw 分布。
3. 展示延迟、成功率、来源占比。
4. 支持删除代理。

### Phase 7：生产化

目标：

1. Prometheus metrics。
2. 结构化日志。
3. GitHub Actions CI。
4. Docker 镜像构建。
5. README 完善。
6. 安全配置说明。
