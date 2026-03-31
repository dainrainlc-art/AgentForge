#!/bin/bash

# ===========================================
# AgentForge 快速构建和部署脚本
# ===========================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印函数
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查 Docker 权限
check_docker() {
    print_info "检查 Docker 权限..."
    if ! docker ps &> /dev/null; then
        print_warning "Docker 权限不足，尝试使用 sudo..."
        USE_SUDO="sudo"
    else
        USE_SUDO=""
    fi
}

# 清理旧构建
clean_build() {
    print_info "清理旧的 Docker 构建缓存..."
    $USE_SUDO docker builder prune -f
    print_success "清理完成"
}

# 构建应用
build_app() {
    print_info "构建 AgentForge 应用..."
    print_info "使用国内镜像源加速构建..."
    
    $USE_SUDO docker-compose -f docker-compose.prod.yml build --no-cache
    
    print_success "应用构建完成"
}

# 启动应用
start_app() {
    print_info "启动 AgentForge 应用服务..."
    
    $USE_SUDO docker-compose -f docker-compose.prod.yml up -d
    
    print_success "应用服务已启动"
}

# 启动监控系统
start_monitoring() {
    print_info "启动监控系统..."
    
    $USE_SUDO docker-compose -f docker-compose.monitoring.yml up -d
    
    print_success "监控系统已启动"
}

# 查看服务状态
show_status() {
    print_info "服务状态:"
    echo ""
    
    print_info "应用服务:"
    $USE_SUDO docker-compose -f docker-compose.prod.yml ps
    
    echo ""
    print_info "监控服务:"
    $USE_SUDO docker-compose -f docker-compose.monitoring.yml ps
    
    echo ""
}

# 测试 API
test_api() {
    print_info "测试 API 健康检查..."
    
    if curl -s http://localhost:8000/api/health &> /dev/null; then
        print_success "API 健康检查通过"
    else
        print_warning "API 尚未就绪，请稍后检查"
    fi
}

# 显示访问信息
show_access_info() {
    print_info "=========================================="
    print_success "AgentForge 部署完成！"
    print_info "=========================================="
    echo ""
    print_info "服务访问地址:"
    echo ""
    print_info "  前端应用：http://localhost"
    print_info "  API 服务：http://localhost:8000"
    print_info "  API 文档：http://localhost:8000/docs"
    print_info "  Grafana:  http://localhost:3000 (admin/admin)"
    print_info "  Prometheus: http://localhost:9090"
    echo ""
    print_info "查看日志:"
    echo "  $USE_SUDO docker-compose -f docker-compose.prod.yml logs -f"
    echo ""
    print_info "停止服务:"
    echo "  $USE_SUDO docker-compose -f docker-compose.prod.yml down"
    echo ""
    print_info "=========================================="
}

# 主函数
main() {
    print_info "开始部署 AgentForge..."
    echo ""
    
    check_docker
    clean_build
    build_app
    start_app
    
    print_info "等待应用启动..."
    sleep 10
    
    start_monitoring
    show_status
    test_api
    show_access_info
}

# 显示帮助
show_help() {
    echo "用法：$0 [选项]"
    echo ""
    echo "选项:"
    echo "  --build-only      只构建不启动"
    echo "  --start-only      只启动不构建"
    echo "  --monitoring      只启动监控系统"
    echo "  --status          查看服务状态"
    echo "  --clean           清理所有容器和卷"
    echo "  --help            显示帮助信息"
    echo ""
    echo "示例:"
    echo "  $0                # 完整部署（构建 + 启动）"
    echo "  $0 --build-only   # 只构建"
    echo "  $0 --start-only   # 只启动"
    echo "  $0 --clean        # 清理所有"
}

# 解析参数
case "${1:-}" in
    --build-only)
        check_docker
        clean_build
        build_app
        ;;
    --start-only)
        check_docker
        start_app
        ;;
    --monitoring)
        check_docker
        start_monitoring
        ;;
    --status)
        check_docker
        show_status
        ;;
    --clean)
        print_warning "清理所有容器和数据卷..."
        $USE_SUDO docker-compose -f docker-compose.prod.yml down -v
        $USE_SUDO docker-compose -f docker-compose.monitoring.yml down -v
        print_success "清理完成"
        ;;
    --help|-h)
        show_help
        ;;
    *)
        main
        ;;
esac
