#!/bin/bash
# AgentForge 基础服务日志查看脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ -z "$1" ]; then
    echo "查看所有服务日志..."
    sudo docker-compose -f docker-compose.base.yml logs -f
else
    echo "查看 $1 服务日志..."
    sudo docker-compose -f docker-compose.base.yml logs -f "$1"
fi
