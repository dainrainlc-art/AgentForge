#!/bin/bash
# AgentForge 基础服务启动脚本
# 使用sudo绕过Docker权限问题

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "AgentForge 基础服务启动脚本"
echo "=========================================="
echo ""

# 检查.env文件是否存在
if [ ! -f ".env" ]; then
    echo "❌ 错误：.env文件不存在！"
    exit 1
fi

# 检查API Key是否配置
source .env
if [ -z "$QIANFAN_API_KEY" ] || [ "$QIANFAN_API_KEY" = "your_qianfan_api_key_here" ]; then
    echo "⚠️  警告：百度千帆API Key未配置！"
    echo "   请在.env文件中配置 QIANFAN_API_KEY"
    echo ""
    read -p "是否继续启动服务？(y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "📦 拉取Docker镜像..."
sudo docker-compose -f docker-compose.base.yml pull
echo ""

echo "🚀 启动基础服务..."
sudo docker-compose -f docker-compose.base.yml up -d
echo ""

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 5
echo ""

# 检查服务状态
echo "📊 服务状态："
sudo docker-compose -f docker-compose.base.yml ps
echo ""

echo "✅ 基础服务启动完成！"
echo ""
echo "=========================================="
echo "服务访问地址："
echo "  N8N:         http://localhost:5678"
echo "  PostgreSQL:  localhost:5432"
echo "  Redis:       localhost:6379"
echo "  Qdrant:      http://localhost:6333"
echo ""
echo "默认凭据："
echo "  N8N用户名:  admin"
echo "  N8N密码:    $N8N_BASIC_AUTH_PASSWORD"
echo ""
echo "查看服务日志："
echo "  sudo docker-compose -f docker-compose.base.yml logs -f"
echo ""
echo "停止服务："
echo "  sudo docker-compose -f docker-compose.base.yml down"
echo "=========================================="
