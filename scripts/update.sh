#!/usr/bin/env bash
set -euo pipefail

# 在项目根执行：
# - 停止并移除旧容器
# - 重新构建镜像（不使用缓存并拉取基础镜像）
# - 以强制重建方式启动容器

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

echo "Stopping and removing existing containers..."
docker-compose down --remove-orphans

echo "Building image (no cache, pulling latest base image)..."
docker-compose build --no-cache --pull

echo "Starting containers..."
docker-compose up -d --force-recreate --remove-orphans

echo "Pruning unused images..."
docker image prune -f

echo "Deployment complete."
