#!/bin/bash
# AgentForge 部署启动脚本

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印函数
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 显示菜单
show_menu() {
    clear
    print_header "AgentForge 部署计划"
    echo "请选择要执行的部署阶段："
    echo ""
    echo "1) Phase 1: 前端完善（Day 1-3）"
    echo "2) Phase 2: CI/CD 和安全（Day 4-10）"
    echo "3) Phase 3: 性能优化（Day 11-20）"
    echo "4) Phase 4: 功能扩展（Day 21-35）"
    echo "5) 查看当前服务状态"
    echo "6) 查看部署文档"
    echo "0) 退出"
    echo ""
}

# Phase 1: 前端完善
phase1_frontend() {
    print_header "Phase 1: 前端完善"
    
    echo "1.1) 检查和安装前端依赖"
    echo "1.2) 构建前端应用"
    echo "1.3) 重新构建 Docker 镜像"
    echo "1.4) 测试前端功能"
    echo "1.5) 返回主菜单"
    echo ""
    
    read -p "请选择操作 [1-5]: " sub_choice
    
    case $sub_choice in
        1)
            print_header "安装前端依赖"
            cd frontend
            if [ -f "package.json" ]; then
                npm install --legacy-peer-deps
                print_success "依赖安装完成"
            else
                print_error "package.json 不存在"
            fi
            cd ..
            ;;
        2)
            print_header "构建前端应用"
            cd frontend
            if [ -f "package.json" ]; then
                npm run build
                print_success "前端构建完成"
            else
                print_error "package.json 不存在"
            fi
            cd ..
            ;;
        3)
            print_header "重新构建 Docker 镜像"
            sudo docker-compose -f docker-compose.prod.yml build agentforge-frontend
            print_success "Docker 镜像构建完成"
            ;;
        4)
            print_header "测试前端功能"
            echo "请在浏览器中访问："
            echo "  - 前端：http://localhost"
            echo "  - API 文档：http://localhost:8000/docs"
            echo ""
            echo "测试项目："
            echo "  ✓ 登录功能"
            echo "  ✓ 聊天功能"
            echo "  ✓ 工作流列表"
            echo "  ✓ 插件管理"
            ;;
        5)
            return
            ;;
        *)
            print_error "无效选择"
            ;;
    esac
    
    echo ""
    read -p "按回车键继续..."
    phase1_frontend
}

# Phase 2: CI/CD 和安全
phase2_cicd() {
    print_header "Phase 2: CI/CD 和安全加固"
    
    echo "2.1) 配置 SSL/HTTPS"
    echo "2.2) 设置 GitHub Actions"
    echo "2.3) 运行安全扫描"
    echo "2.4) 返回主菜单"
    echo ""
    
    read -p "请选择操作 [1-4]: " sub_choice
    
    case $sub_choice in
        1)
            print_header "配置 SSL/HTTPS"
            if [ -f "scripts/update-ssl-cert.sh" ]; then
                sudo ./scripts/update-ssl-cert.sh
                print_success "SSL 证书配置完成"
            else
                print_error "SSL 脚本不存在"
            fi
            ;;
        2)
            print_header "设置 GitHub Actions"
            echo "请查看 docs/DEPLOYMENT_PLAN_DETAILED.md 中的 CI/CD 配置示例"
            echo ""
            echo "创建 .github/workflows/ci.yml 文件"
            ;;
        3)
            print_header "运行安全扫描"
            echo "安装安全扫描工具..."
            pip install safety bandit -q
            
            echo ""
            echo "扫描依赖漏洞..."
            safety check || true
            
            echo ""
            echo "扫描代码安全..."
            bandit -r agentforge/ || true
            ;;
        4)
            return
            ;;
        *)
            print_error "无效选择"
            ;;
    esac
    
    echo ""
    read -p "按回车键继续..."
    phase2_cicd
}

# Phase 3: 性能优化
phase3_performance() {
    print_header "Phase 3: 性能优化"
    
    echo "3.1) 数据库性能分析"
    echo "3.2) 缓存优化"
    echo "3.3) API 性能测试"
    echo "3.4) 返回主菜单"
    echo ""
    
    read -p "请选择操作 [1-4]: " sub_choice
    
    case $sub_choice in
        1)
            print_header "数据库性能分析"
            echo "连接到数据库..."
            sudo docker-compose -f docker-compose.prod.yml exec postgres psql -U agentforge -d agentforge -c "EXPLAIN ANALYZE SELECT * FROM users LIMIT 10;"
            ;;
        2)
            print_header "缓存优化"
            echo "测试 Redis 连接..."
            sudo docker-compose -f docker-compose.prod.yml exec redis redis-cli ping
            ;;
        3)
            print_header "API 性能测试"
            echo "使用 ab 进行压力测试..."
            if command -v ab &> /dev/null; then
                ab -n 1000 -c 10 http://localhost:8000/api/health
            else
                print_warning "ab 未安装，使用 curl 测试"
                time curl -s http://localhost:8000/api/health
            fi
            ;;
        4)
            return
            ;;
        *)
            print_error "无效选择"
            ;;
    esac
    
    echo ""
    read -p "按回车键继续..."
    phase3_performance
}

# Phase 4: 功能扩展
phase4_features() {
    print_header "Phase 4: 功能扩展"
    
    echo "4.1) 查看移动端开发计划"
    echo "4.2) 查看插件开发计划"
    echo "4.3) 返回主菜单"
    echo ""
    
    read -p "请选择操作 [1-3]: " sub_choice
    
    case $sub_choice in
        1)
            print_header "移动端开发计划"
            echo "请查看 docs/NEXT_STEPS_TODO_LIST.md 中的移动端应用部分"
            echo ""
            echo "技术选型："
            echo "  - React Native"
            echo "  - Flutter"
            ;;
        2)
            print_header "插件开发计划"
            echo "请查看 docs/NEXT_STEPS_TODO_LIST.md 中的插件开发部分"
            echo ""
            echo "计划开发的插件："
            echo "  - 天气插件"
            echo "  - 货币转换插件"
            echo "  - 日历插件"
            echo "  - 文件处理插件"
            ;;
        3)
            return
            ;;
        *)
            print_error "无效选择"
            ;;
    esac
    
    echo ""
    read -p "按回车键继续..."
    phase4_features
}

# 查看服务状态
check_status() {
    print_header "服务状态检查"
    
    echo "检查 Docker 服务..."
    sudo docker-compose -f docker-compose.prod.yml ps
    
    echo ""
    echo "检查 API 健康..."
    if curl -s http://localhost:8000/api/health > /dev/null; then
        print_success "API 服务正常"
        curl -s http://localhost:8000/api/health | python3 -m json.tool 2>/dev/null || curl -s http://localhost:8000/api/health
    else
        print_error "API 服务不可达"
    fi
    
    echo ""
    read -p "按回车键继续..."
}

# 查看文档
view_docs() {
    print_header "部署文档"
    
    echo "可用文档："
    echo "  1. docs/NEXT_STEPS_TODO_LIST.md - 待开发任务清单"
    echo "  2. docs/DEPLOYMENT_PLAN_DETAILED.md - 详细部署计划"
    echo "  3. docs/QUICK_START_GUIDE.md - 快速开始指南"
    echo ""
    
    read -p "选择要查看的文档 [1-3]: " doc_choice
    
    case $doc_choice in
        1)
            less docs/NEXT_STEPS_TODO_LIST.md
            ;;
        2)
            less docs/DEPLOYMENT_PLAN_DETAILED.md
            ;;
        3)
            less docs/QUICK_START_GUIDE.md
            ;;
        *)
            print_error "无效选择"
            ;;
    esac
}

# 主循环
while true; do
    show_menu
    read -p "请输入选择 [0-6]: " choice
    
    case $choice in
        1)
            phase1_frontend
            ;;
        2)
            phase2_cicd
            ;;
        3)
            phase3_performance
            ;;
        4)
            phase4_features
            ;;
        5)
            check_status
            ;;
        6)
            view_docs
            ;;
        0)
            clear
            print_header "部署脚本退出"
            echo "感谢使用！"
            echo ""
            echo "提示："
            echo "  - 查看详细文档：less docs/NEXT_STEPS_TODO_LIST.md"
            echo "  - 查看服务状态：./service-manager.sh status"
            echo "  - 重启服务：./service-manager.sh restart"
            echo ""
            exit 0
            ;;
        *)
            print_error "无效选择，请重新输入"
            sleep 2
            ;;
    esac
done
