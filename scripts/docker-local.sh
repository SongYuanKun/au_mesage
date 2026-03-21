#!/usr/bin/env bash
# 本地 Docker 启动应用（MySQL 须为外部实例，见 README / .env.example）
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p logs
if [[ ! -f .env ]]; then
  echo "未找到 .env，从 .env.example 复制；请编辑 MYSQL_PASSWORD，若 MySQL 在宿主机请设 MYSQL_HOST=host.docker.internal"
  cp .env.example .env
fi
exec docker compose up --build "$@"
