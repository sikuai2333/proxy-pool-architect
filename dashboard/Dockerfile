FROM node:20-alpine AS build

WORKDIR /app
ENV CI=true
ENV COREPACK_ENABLE_DOWNLOAD_PROMPT=0

COPY package.json pnpm-lock.yaml ./
RUN corepack enable && pnpm install --frozen-lockfile

COPY . .

ARG VITE_DASHBOARD_DATA_MODE=live
ARG VITE_API_BASE_URL=/api
ARG VITE_API_REQUEST_TIMEOUT_MS=4000

ENV VITE_DASHBOARD_DATA_MODE=${VITE_DASHBOARD_DATA_MODE}
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
ENV VITE_API_REQUEST_TIMEOUT_MS=${VITE_API_REQUEST_TIMEOUT_MS}

RUN pnpm build

FROM nginx:1.27-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
