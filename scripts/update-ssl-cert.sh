# ===========================================
# SSL/HTTPS 证书自动更新脚本
# 使用 Let's Encrypt 免费证书
# ===========================================

#!/bin/bash

set -e

# 配置变量
DOMAIN="${DOMAIN_NAME:-your-domain.com}"
EMAIL="${ADMIN_EMAIL:-admin@example.com}"
WEBROOT="/var/www/certbot"
CERT_PATH="/etc/letsencrypt/live/${DOMAIN}"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查 certbot 是否安装
check_certbot() {
    if ! command -v certbot &> /dev/null; then
        log_error "certbot 未安装，正在安装..."
        apt-get update && apt-get install -y certbot python3-certbot-nginx
    fi
}

# 创建 webroot 目录
create_webroot() {
    if [ ! -d "$WEBROOT" ]; then
        log_info "创建 webroot 目录：$WEBROOT"
        mkdir -p "$WEBROOT"
    fi
}

# 申请证书
request_certificate() {
    log_info "申请 Let's Encrypt 证书：$DOMAIN"
    
    certbot certonly \
        --webroot \
        --webroot-path="$WEBROOT" \
        --email "$EMAIL" \
        --agree-tos \
        --no-eff-email \
        --force-renewal \
        -d "$DOMAIN" \
        -d "www.$DOMAIN"
    
    if [ $? -eq 0 ]; then
        log_info "证书申请成功！"
    else
        log_error "证书申请失败！"
        exit 1
    fi
}

# 更新证书
renew_certificate() {
    log_info "检查证书是否需要更新..."
    
    certbot renew \
        --webroot \
        --webroot-path="$WEBROOT" \
        --quiet \
        --dry-run
    
    if [ $? -eq 0 ]; then
        log_info "证书更新检查通过"
        
        # 实际更新（去掉 dry-run）
        certbot renew \
            --webroot \
            --webroot-path="$WEBROOT" \
            --quiet
        
        if [ $? -eq 0 ]; then
            log_info "证书更新成功！"
            
            # 重新加载 Nginx
            log_info "重新加载 Nginx 配置..."
            nginx -t && systemctl reload nginx
        else
            log_error "证书更新失败！"
            exit 1
        fi
    else
        log_warn "证书更新检查失败，请手动检查"
    fi
}

# 部署证书到 Nginx
deploy_certificate() {
    log_info "部署证书到 Nginx..."
    
    # 复制证书到 Nginx 目录
    cp "${CERT_PATH}/fullchain.pem" /etc/nginx/ssl/
    cp "${CERT_PATH}/privkey.pem" /etc/nginx/ssl/
    
    # 设置权限
    chmod 644 /etc/nginx/ssl/fullchain.pem
    chmod 600 /etc/nginx/ssl/privkey.pem
    
    log_info "证书部署完成"
}

# 主函数
main() {
    case "${1:-renew}" in
        request)
            check_certbot
            create_webroot
            request_certificate
            deploy_certificate
            ;;
        renew)
            renew_certificate
            deploy_certificate
            ;;
        deploy)
            deploy_certificate
            ;;
        *)
            echo "用法：$0 {request|renew|deploy}"
            exit 1
            ;;
    esac
}

main "$@"
