#!/bin/bash

# Docker部署优化脚本

set -e

echo "🚀 开始Docker部署优化..."

# 检查Docker和Docker Compose
if ! command -v docker &> /dev/null; then
    echo "❌ Docker未安装"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose未安装"
    exit 1
fi

# 清理旧镜像和容器
echo "🧹 清理旧资源..."
docker-compose down --remove-orphans || true
docker system prune -f

# 构建优化镜像
echo "🔨 构建优化镜像..."
if [ -f "Dockerfile.production" ]; then
    docker-compose -f docker-compose.optimized.yml build --no-cache
else
    docker-compose build --no-cache
fi

# 启动服务
echo "🚀 启动服务..."
if [ -f "docker-compose.optimized.yml" ]; then
    docker-compose -f docker-compose.optimized.yml up -d
else
    docker-compose up -d
fi

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 健康检查
echo "🔍 执行健康检查..."
if curl -f http://localhost:8083/health > /dev/null 2>&1; then
    echo "✅ 服务启动成功！"
else
    echo "❌ 服务启动失败"
    docker-compose logs
    exit 1
fi

# 显示容器状态
echo "📊 容器状态："
docker-compose ps

# 显示资源使用情况
echo "💾 资源使用情况："
docker stats --no-stream

echo "🎉 部署完成！"
echo "📝 查看日志: docker-compose logs -f"
echo "🛑 停止服务: docker-compose down"
