#!/usr/bin/env bash
# 本地 Docker：应用 + 内置 MySQL（docker-compose.mysql.yml）
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p logs
if [[ ! -f .env.mysql ]]; then
  echo "未找到 .env.mysql，从 .env.mysql.example 复制；请编辑 MYSQL_PASSWORD"
  cp .env.mysql.example .env.mysql
fi
exec docker compose --env-file .env.mysql -f docker-compose.mysql.yml up --build "$@"
