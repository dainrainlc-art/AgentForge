#!/bin/bash
# AgentForge 启动脚本

echo "=========================================="
echo "AgentForge - Fiverr运营自动化智能助理系统"
echo "=========================================="
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "❌ 虚拟环境不存在，请先运行: python3 -m venv venv"
    exit 1
fi

# 激活虚拟环境
echo "🔧 激活虚拟环境..."
source venv/bin/activate

# 检查.env文件
if [ ! -f ".env" ]; then
    echo "❌ .env文件不存在！"
    exit 1
fi

echo ""
echo "🚀 启动AgentForge API服务器..."
echo ""
echo "服务地址: http://localhost:8000"
echo "API文档: http://localhost:8000/docs"
echo ""
echo "按 Ctrl+C 停止服务"
echo "=========================================="
echo ""

# 启动FastAPI服务器
python -m uvicorn src.agentforge.api.main:app --host 0.0.0.0 --port 8000 --reload
