# NAS Docker 部署与登录鉴权说明

本文档给出一套最直接的部署方式：

- 不依赖 GitHub Actions
- 直接部署到可运行 Docker 的 NAS
- Dashboard 使用账号密码登录
- API 同时支持浏览器登录态和 Basic Auth

## 1. 推荐部署结构

推荐使用当前仓库根目录的 `compose.yml`：

- `redis`：内部服务，不对外暴露
- `api`：FastAPI 后端，容器内监听 `8000`
- `dashboard`：Nginx + 前端静态资源，对外暴露 `8080`

浏览器只访问：

```text
http://<NAS-IP>:8080
```

前端再通过同域路径访问后端：

```text
http://<NAS-IP>:8080/api/*
```

这样做的好处是：

- 登录 Cookie 和前端页面同域
- 不需要单独处理浏览器跨域登录
- 部署结构简单，适合 NAS

## 2. 部署前准备

确认 NAS 已安装并启用：

- Docker
- Docker Compose

把整个项目目录复制到 NAS，例如：

```text
/volume1/docker/proxy-pool-architect
```

## 3. 生成生产环境文件

在项目根目录执行：

```bash
cp .env.prod.example .env.prod
```

如果 NAS 是 BusyBox/Alpine 环境，也可以直接手工创建 `.env.prod`。

## 4. 最小可用配置

编辑 `.env.prod`，至少确认这些项：

```env
APP_ENV=prod

AUTH_ENABLED=true
AUTH_ADMIN_USERNAME=admin
AUTH_ADMIN_PASSWORD=change-me-strong-password

ALLOWED_HOSTS=localhost,127.0.0.1,192.168.1.10,nas.local
CORS_ALLOWED_ORIGINS=[]
CORS_ALLOW_CREDENTIALS=false

AUTH_SESSION_SECURE=false
AUTH_SESSION_SAMESITE=lax

REDIS_URL=redis://redis:6379/0
SCHEDULER_ENABLED=true
```

说明：

- `AUTH_ENABLED=true`：开启管理登录
- `AUTH_ADMIN_USERNAME` / `AUTH_ADMIN_PASSWORD`：Dashboard 登录账号密码，同时也用于 API Basic Auth
- `ALLOWED_HOSTS`：填写你的 NAS IP、域名，多个值用逗号分隔
- `CORS_ALLOWED_ORIGINS=[]`：当前推荐同域 `/api` 部署，所以这里保持空列表即可
- `AUTH_SESSION_SECURE=false`：如果你现在只是 NAS 局域网 HTTP 访问，先保持 `false`
- 如果你后面接了 HTTPS 反向代理，再改成 `AUTH_SESSION_SECURE=true`

## 5. 启动服务

在项目根目录执行：

```bash
docker compose up -d --build
```

查看状态：

```bash
docker compose ps
```

正常情况下应看到：

- `redis` healthy
- `api` healthy
- `dashboard` healthy

## 6. 访问方式

### 浏览器登录 Dashboard

打开：

```text
http://<NAS-IP>:8080
```

输入：

- 用户名：你在 `.env.prod` 配置的 `AUTH_ADMIN_USERNAME`
- 密码：你在 `.env.prod` 配置的 `AUTH_ADMIN_PASSWORD`

登录成功后，前端会通过 `HttpOnly` Cookie 持续访问 `/api/*`。

### 直接调用 API

如果你不走浏览器，而是脚本、curl、其他程序直接调接口，建议使用 Basic Auth。

示例：

```bash
curl -u "admin:change-me-strong-password" "http://<NAS-IP>:8080/api/stats"
```

获取代理列表：

```bash
curl -u "admin:change-me-strong-password" "http://<NAS-IP>:8080/api/proxy/list?pool=elite&limit=20&offset=0"
```

## 7. 登录相关接口

当前后端已经支持以下鉴权接口：

### 查询当前登录状态

```bash
curl "http://<NAS-IP>:8080/api/auth/session"
```

未登录时返回：

```json
{
  "enabled": true,
  "authenticated": false,
  "username": null,
  "expires_at": null,
  "auth_method": null
}
```

### 登录

```bash
curl -X POST "http://<NAS-IP>:8080/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"change-me-strong-password"}'
```

### 退出登录

```bash
curl -X POST "http://<NAS-IP>:8080/api/auth/logout"
```

## 8. 更新方式

如果你直接在 NAS 本机维护代码：

```bash
docker compose down
docker compose up -d --build
```

如果你在本地电脑构建镜像，再传到 NAS：

```bash
docker build -t proxy-pool-architect:local .
docker build -t proxy-pool-dashboard:local ./dashboard
docker save -o proxy-pool-images.tar proxy-pool-architect:local proxy-pool-dashboard:local redis:7-alpine
```

拷到 NAS 后：

```bash
docker load -i proxy-pool-images.tar
docker compose up -d
```

## 9. 常见问题

### 1）浏览器能打开页面，但接口返回 401

这是正常行为，说明鉴权已开启但你还没登录。

先访问：

```text
http://<NAS-IP>:8080
```

登录后再看页面数据。

### 2）脚本请求接口一直 401

脚本默认没有浏览器 Cookie，这时请使用 Basic Auth：

```bash
curl -u "admin:change-me-strong-password" "http://<NAS-IP>:8080/api/stats"
```

### 3）容器启动后 `api` unhealthy

优先检查：

- `.env.prod` 是否写错
- `ALLOWED_HOSTS` 是否是逗号分隔或 JSON 数组格式
- `AUTH_ENABLED=true` 时是否同时配置了账号密码

查看日志：

```bash
docker compose logs --tail=100 api
```

### 4）公网访问是否需要额外处理

需要。

如果不是只在局域网使用，至少再补这几项：

- HTTPS 反向代理
- `AUTH_SESSION_SECURE=true`
- 更强的管理员密码
- 只开放必要端口
- 定期更新镜像

## 10. 当前建议

如果你现在只是先在 NAS 内网自用，建议先按下面这套跑起来：

1. `AUTH_ENABLED=true`
2. 通过 `dashboard:8080` 统一访问
3. 浏览器登录 Dashboard
4. 脚本侧使用 Basic Auth
5. 暂时不拆分前后端域名

这是当前最稳、最省事的落地方式。

## 11. 如果 NAS 面板要求上传 compose.yml

如果你的 NAS 面板是“项目 / Stack / Compose”形式创建，可以直接使用仓库根目录的
`compose.yml`。

创建前需要确保同目录下已经有 `.env.prod`，否则 `api` 容器会因为找不到配置文件而启动失败。

目录结构应类似：

```text
proxy-pool-architect/
  compose.yml
  .env.prod
  Dockerfile
  dashboard/
  app/
  config/
```

如果你仍想使用旧文件名，也可以运行：

```bash
docker compose -f docker-compose.prod.yml up -d --build
```
