#!/bin/bash

# ===========================================
# AgentForge 简易部署脚本（无需 sudo）
# ===========================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

print_info "开始部署 AgentForge（简易模式）..."
echo ""

# 检查 Docker 是否可用
print_info "检查 Docker 连接..."
if ! docker ps &> /dev/null; then
    print_error "无法连接到 Docker！"
    print_error "请尝试以下方案："
    echo ""
    echo "方案 1: 重新登录系统"
    echo "  exit"
    echo "  # 然后重新 SSH 登录或打开新终端"
    echo ""
    echo "方案 2: 重启 Docker 服务（需要 root）"
    echo "  sudo systemctl restart docker"
    echo ""
    echo "方案 3: 使用当前用户直接运行 docker 命令"
    echo "  如果 docker ps 可以运行，请重新执行此脚本"
    exit 1
fi

print_success "Docker 连接正常"
echo ""

# 测试网络
print_info "测试网络连接..."
if ping -c 1 mirrors.aliyun.com &> /dev/null; then
    print_success "阿里云镜像源可访问"
else
    print_warning "阿里云镜像源不可访问，构建可能失败"
fi
echo ""

# 构建应用
print_info "构建 AgentForge 应用..."
print_info "这一步可能需要 5-10 分钟..."
echo ""

docker-compose -f docker-compose.prod.yml build --no-cache

if [ $? -eq 0 ]; then
    print_success "应用构建成功！"
else
    print_error "应用构建失败！"
    print_error "请检查网络或 Docker 配置"
    exit 1
fi

echo ""
print_info "启动应用服务..."
docker-compose -f docker-compose.prod.yml up -d

if [ $? -eq 0 ]; then
    print_success "应用服务已启动！"
else
    print_error "应用服务启动失败！"
    exit 1
fi

echo ""
print_info "等待应用启动..."
sleep 15

echo ""
print_info "启动监控系统..."
docker-compose -f docker-compose.monitoring.yml up -d

if [ $? -eq 0 ]; then
    print_success "监控系统已启动！"
else
    print_warning "监控系统启动失败，但应用仍可正常运行"
fi

echo ""
print_info "=========================================="
print_success "AgentForge 部署完成！"
print_info "=========================================="
echo ""
print_info "服务状态:"
docker-compose -f docker-compose.prod.yml ps
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
echo "  docker-compose -f docker-compose.prod.yml logs -f"
echo ""
print_info "停止服务:"
echo "  docker-compose -f docker-compose.prod.yml down"
echo ""
print_info "=========================================="
