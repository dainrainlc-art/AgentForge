#!/bin/bash
# AgentForge 服务管理脚本

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

COMPOSE_FILE="docker-compose.prod.yml"

show_help() {
    echo "AgentForge 服务管理脚本"
    echo ""
    echo "用法: $0 [命令]"
    echo ""
    echo "命令:"
    echo "  start    - 启动所有服务"
    echo "  stop     - 停止所有服务"
    echo "  restart  - 重启所有服务"
    echo "  status   - 查看服务状态"
    echo "  logs     - 查看服务日志"
    echo "  build    - 重新构建镜像"
    echo "  health   - 检查 API 健康状态"
    echo "  help     - 显示帮助信息"
    echo ""
    echo "服务访问地址:"
    echo "  - 前端界面:    http://localhost"
    echo "  - API 服务:    http://localhost:8000"
    echo "  - API 文档:    http://localhost:8000/docs"
    echo "  - N8N 工作流:  http://localhost:5678"
    echo ""
}

start_services() {
    echo "🚀 启动 AgentForge 服务..."
    sudo docker-compose -f "$COMPOSE_FILE" up -d
    echo "✅ 服务启动中，请稍候..."
    sleep 10
    check_status
}

stop_services() {
    echo "🛑 停止 AgentForge 服务..."
    sudo docker-compose -f "$COMPOSE_FILE" down
    echo "✅ 服务已停止"
}

restart_services() {
    echo "🔄 重启 AgentForge 服务..."
    stop_services
    sleep 3
    start_services
}

check_status() {
    echo "📊 服务状态:"
    echo ""
    sudo docker-compose -f "$COMPOSE_FILE" ps
    echo ""
    echo "🩺 API 健康检查:"
    if curl -s http://localhost:8000/api/health > /dev/null; then
        echo "✅ API 服务正常"
        curl -s http://localhost:8000/api/health | python3 -m json.tool 2>/dev/null || curl -s http://localhost:8000/api/health
    else
        echo "❌ API 服务不可达"
    fi
}

view_logs() {
    echo "📋 查看服务日志 (Ctrl+C 退出):"
    sudo docker-compose -f "$COMPOSE_FILE" logs -f
}

build_images() {
    echo "🔨 重新构建 Docker 镜像..."
    sudo docker-compose -f "$COMPOSE_FILE" build --no-cache
    echo "✅ 镜像构建完成"
}

check_health() {
    echo "🩺 检查 API 健康状态..."
    if curl -s http://localhost:8000/api/health > /dev/null; then
        echo "✅ API 服务正常运行"
        echo ""
        curl -s http://localhost:8000/api/health | python3 -m json.tool 2>/dev/null || curl -s http://localhost:8000/api/health
    else
        echo "❌ API 服务不可达，请检查服务是否启动"
        exit 1
    fi
}

case "$1" in
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    restart)
        restart_services
        ;;
    status)
        check_status
        ;;
    logs)
        view_logs
        ;;
    build)
        build_images
        ;;
    health)
        check_health
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "❌ 未知命令: $1"
        echo ""
        show_help
        exit 1
        ;;
esac
