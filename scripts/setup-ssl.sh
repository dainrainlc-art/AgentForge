#!/bin/bash
# AgentForge SSL Certificate Auto-Renewal Setup Script
# Uses Let's Encrypt with Certbot

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

DOMAIN="${1:-}"
EMAIL="${2:-admin@${DOMAIN}}"

if [ -z "$DOMAIN" ]; then
    echo "Usage: $0 <domain> [email]"
    echo "Example: $0 example.com admin@example.com"
    exit 1
fi

echo "=========================================="
echo "AgentForge SSL Certificate Setup"
echo "Domain: $DOMAIN"
echo "Email: $EMAIL"
echo "=========================================="

check_dependencies() {
    echo "[1/6] Checking dependencies..."
    
    if ! command -v certbot &> /dev/null; then
        echo "Installing certbot..."
        if command -v apt-get &> /dev/null; then
            sudo apt-get update
            sudo apt-get install -y certbot python3-certbot-nginx
        elif command -v yum &> /dev/null; then
            sudo yum install -y certbot python3-certbot-nginx
        elif command -v dnf &> /dev/null; then
            sudo dnf install -y certbot python3-certbot-nginx
        else
            echo "Please install certbot manually"
            exit 1
        fi
    fi
    
    echo "Certbot installed: $(certbot --version)"
}

setup_nginx_ssl() {
    echo "[2/6] Setting up Nginx SSL configuration..."
    
    SSL_CONF="$PROJECT_ROOT/docker/nginx/ssl.conf"
    mkdir -p "$(dirname "$SSL_CONF")"
    
    cat > "$SSL_CONF" << EOF
# SSL Configuration for $DOMAIN
ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;

# SSL Security Settings
ssl_protocols TLSv1.2 TLSv1.3;
ssl_prefer_server_ciphers on;
ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
ssl_session_timeout 1d;
ssl_session_cache shared:SSL:50m;
ssl_session_tickets off;

# HSTS
add_header Strict-Transport-Security "max-age=63072000" always;

# OCSP Stapling
ssl_stapling on;
ssl_stapling_verify on;
resolver 8.8.8.8 8.8.4.4 valid=300s;
resolver_timeout 5s;
EOF
    
    echo "SSL configuration created: $SSL_CONF"
}

create_nginx_site() {
    echo "[3/6] Creating Nginx site configuration..."
    
    SITE_CONF="$PROJECT_ROOT/docker/nginx/sites/$DOMAIN.conf"
    mkdir -p "$(dirname "$SITE_CONF")"
    
    cat > "$SITE_CONF" << 'EOF'
# HTTP to HTTPS redirect
server {
    listen 80;
    listen [::]:80;
    server_name DOMAIN_PLACEHOLDER;
    
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    
    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name DOMAIN_PLACEHOLDER;
    
    include /etc/nginx/ssl.conf;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/json application/xml;
    
    # Frontend
    location / {
        proxy_pass http://frontend:5173;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
    
    # Backend API
    location /api/ {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }
    
    # WebSocket
    location /ws/ {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
    
    # N8N
    location /n8n/ {
        proxy_pass http://n8n:5678/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF
    
    sed -i "s/DOMAIN_PLACEHOLDER/$DOMAIN/g" "$SITE_CONF"
    echo "Site configuration created: $SITE_CONF"
}

setup_certbot_renewal() {
    echo "[4/6] Setting up certbot renewal cron job..."
    
    CRON_JOB="0 0,12 * * * root certbot renew --quiet --post-hook 'docker restart nginx'"
    
    if [ -f /etc/cron.d/certbot ]; then
        echo "Certbot cron job already exists"
    else
        echo "$CRON_JOB" | sudo tee /etc/cron.d/certbot > /dev/null
        sudo chmod 644 /etc/cron.d/certbot
        echo "Cron job created: /etc/cron.d/certbot"
    fi
}

create_docker_compose_ssl() {
    echo "[5/6] Creating Docker Compose SSL configuration..."
    
    COMPOSE_SSL="$PROJECT_ROOT/docker-compose.ssl.yml"
    
    cat > "$COMPOSE_SSL" << 'EOF'
version: '3.8'

services:
  nginx:
    image: nginx:alpine
    container_name: agentforge-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./docker/nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./docker/nginx/sites:/etc/nginx/sites:ro
      - ./docker/nginx/ssl.conf:/etc/nginx/ssl.conf:ro
      - certbot-etc:/etc/letsencrypt
      - certbot-var:/var/lib/letsencrypt
      - ./docker/nginx/www:/var/www/certbot
    depends_on:
      - backend
      - frontend
    networks:
      - agentforge-network

  certbot:
    image: certbot/certbot
    container_name: agentforge-certbot
    volumes:
      - certbot-etc:/etc/letsencrypt
      - certbot-var:/var/lib/letsencrypt
      - ./docker/nginx/www:/var/www/certbot
    entrypoint: "/bin/sh -c 'trap exit TERM; while :; do certbot renew; sleep 12h & wait $${!}; done;'"
    networks:
      - agentforge-network

volumes:
  certbot-etc:
  certbot-var:

networks:
  agentforge-network:
    external: true
EOF
    
    echo "Docker Compose SSL config created: $COMPOSE_SSL"
}

create_renewal_script() {
    echo "[6/6] Creating renewal script..."
    
    RENEWAL_SCRIPT="$PROJECT_ROOT/scripts/renew-ssl.sh"
    
    cat > "$RENEWAL_SCRIPT" << 'EOF'
#!/bin/bash
# SSL Certificate Renewal Script

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "Starting SSL certificate renewal..."

# Check if certificates need renewal
if docker exec agentforge-certbot certbot renew --dry-run 2>&1 | grep -q "No renewals were attempted"; then
    echo "Certificates are up to date"
    exit 0
fi

# Renew certificates
echo "Renewing certificates..."
docker exec agentforge-certbot certbot renew --quiet

# Reload Nginx
echo "Reloading Nginx..."
docker exec agentforge-nginx nginx -s reload

echo "SSL renewal completed successfully!"
EOF
    
    chmod +x "$RENEWAL_SCRIPT"
    echo "Renewal script created: $RENEWAL_SCRIPT"
}

print_instructions() {
    echo ""
    echo "=========================================="
    echo "SSL Setup Complete!"
    echo "=========================================="
    echo ""
    echo "Next steps:"
    echo ""
    echo "1. Obtain initial certificate:"
    echo "   sudo certbot certonly --webroot -w $PROJECT_ROOT/docker/nginx/www -d $DOMAIN --email $EMAIL --agree-tos --no-eff-email"
    echo ""
    echo "2. Start services with SSL:"
    echo "   docker-compose -f docker-compose.yml -f docker-compose.ssl.yml up -d"
    echo ""
    echo "3. Test auto-renewal:"
    echo "   sudo certbot renew --dry-run"
    echo ""
    echo "4. Check certificate status:"
    echo "   sudo certbot certificates"
    echo ""
    echo "Certificate files location:"
    echo "   /etc/letsencrypt/live/$DOMAIN/fullchain.pem"
    echo "   /etc/letsencrypt/live/$DOMAIN/privkey.pem"
    echo ""
}

main() {
    check_dependencies
    setup_nginx_ssl
    create_nginx_site
    setup_certbot_renewal
    create_docker_compose_ssl
    create_renewal_script
    print_instructions
}

main
