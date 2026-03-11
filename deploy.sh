#!/bin/bash

# 🦞 ClawChats 快速部署脚本
# 适用于 Linux/macOS

set -e

echo "🦞 ClawChats 快速部署"
echo "======================"
echo ""

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo "❌ 未检测到 Docker，请先安装 Docker"
    echo "   访问：https://www.docker.com/products/docker-desktop/"
    exit 1
fi

# 检查 Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ 未检测到 Docker Compose，请先安装"
    exit 1
fi

echo "✅ Docker 版本：$(docker --version)"
echo "✅ Docker Compose 版本：$(docker-compose --version)"
echo ""

# 启动服务
echo "🚀 启动服务..."
docker-compose up -d

echo ""
echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
echo ""
echo "📊 服务状态:"
docker-compose ps

echo ""
echo "✅ 部署完成！"
echo ""
echo "🌐 访问地址:"
echo "   管理后台：http://localhost:8081"
echo "   用户聊天：http://localhost:8080"
echo ""
echo "🔐 默认管理员账号:"
echo "   用户名：admin"
echo "   密码：Admin@123"
echo ""
echo "⚠️  首次登录后请立即修改密码！"
echo ""
echo "📖 详细文档：DEPLOY.md"
echo ""
