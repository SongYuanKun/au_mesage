#!/bin/bash

# 重新部署脚本
# 停止并移除现有容器，重建镜像并启动新容器

echo "停止并移除现有容器..."
docker compose down

echo "重建镜像..."
docker compose build --no-cache

echo "启动服务..."
docker compose up -d

echo "重新部署完成。服务运行在 http://localhost:8083"