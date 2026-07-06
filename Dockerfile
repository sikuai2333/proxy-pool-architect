# ── build frontend ─────────────────────────────────────────────
FROM node:20-slim AS frontend
WORKDIR /build
COPY dashboard/package.json dashboard/pnpm-lock.yaml ./
RUN corepack enable pnpm && pnpm install --frozen-lockfile --no-dir
COPY dashboard/ ./
RUN pnpm build

# ── runtime ────────────────────────────────────────────────────
FROM python:3.11-slim
WORKDIR /app

COPY pyproject.toml ./
COPY app/ app/
RUN pip install --no-cache-dir . && rm -rf /tmp/pip-*

COPY config/ config/
COPY --from=frontend /build/dist dashboard/dist
RUN mkdir -p /app/data

ENV APP_HOST=0.0.0.0
ENV APP_PORT=8000
ENV DB_PATH=/app/data/proxy_pool.db
ENV SCHEDULER_ENABLED=true

EXPOSE 8000
VOLUME ["/app/data"]

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
