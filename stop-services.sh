#!/bin/bash
# AgentForge 基础服务停止脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "AgentForge 基础服务停止脚本"
echo "=========================================="
echo ""

read -p "确认停止所有服务？(y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 0
fi

echo "🛑 停止服务..."
sudo docker-compose -f docker-compose.base.yml down
echo ""

echo "✅ 服务已停止！"
