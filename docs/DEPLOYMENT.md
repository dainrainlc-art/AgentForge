# AgentForge 部署指南

> 生产环境部署完整指南，包括 Docker 部署、监控配置、备份恢复

---

## 📖 目录

1. [生产环境配置](#生产环境配置)
2. [Docker 部署步骤](#docker-部署步骤)
3. [监控配置](#监控配置)
4. [备份和恢复流程](#备份和恢复流程)

---

## 🏭 生产环境配置

### 系统要求

#### 硬件要求

| 资源 | 最低配置 | 推荐配置 |
|------|----------|----------|
| CPU | 4 核心 | 8 核心+ |
| 内存 | 8GB | 16GB+ |
| 存储 | 50GB SSD | 100GB+ SSD |
| 网络 | 稳定互联网 | 100Mbps+ |

#### 软件要求

| 软件 | 版本要求 | 说明 |
|------|----------|------|
| Docker | 24+ | 容器化运行环境 |
| Docker Compose | 2.20+ | 服务编排 |
| Linux | Ubuntu 20.04+ | 推荐操作系统 |

### 环境变量配置

#### 创建环境变量文件

```bash
# 复制模板
cp .env.example .env.production

# 编辑生产环境配置
vim .env.production
```

#### 必需的环境变量

```bash
# ===========================================
# 百度千帆配置 (必需)
# ===========================================
QIANFAN_API_KEY=your_qianfan_api_key_here

# ===========================================
# 数据库配置
# ===========================================
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=agentforge
POSTGRES_USER=agentforge
POSTGRES_PASSWORD=your_secure_postgres_password

# ===========================================
# Redis 配置
# ===========================================
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password

# ===========================================
# Qdrant 配置
# ===========================================
QDRANT_HOST=qdrant
QDRANT_PORT=6333

# ===========================================
# n8n 配置
# ===========================================
N8N_PORT=5678
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=your_n8n_password
N8N_WEBHOOK_URL=http://n8n:5678/webhook/

# ===========================================
# 系统配置
# ===========================================
TZ=Asia/Shanghai
LOG_LEVEL=INFO
DEBUG_MODE=false

# ===========================================
# 安全配置
# ===========================================
SECRET_KEY=your_secret_key_for_encryption
ENCRYPTION_KEY=your_aes_256_encryption_key

# ===========================================
# 外部访问配置
# ===========================================
PUBLIC_DOMAIN=your-domain.com
WEBHOOK_URL=https://your-domain.com/webhook/
```

#### 生成安全密钥

```bash
# 生成 SECRET_KEY
openssl rand -hex 32

# 生成 ENCRYPTION_KEY (AES-256)
openssl rand -base64 32
```

### 数据库配置

#### 连接池配置

```python
# agentforge/core/config.py
DATABASE_CONFIG = {
    "pool_size": 20,          # 连接池大小
    "max_overflow": 10,       # 最大溢出连接数
    "pool_timeout": 30,       # 获取连接超时
    "pool_recycle": 3600,     # 连接回收时间
    "pool_pre_ping": True,    # 连接前 ping 测试
}
```

#### 索引优化

确保数据库索引已创建：

```sql
-- 查看现有索引
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE schemaname = 'public';

-- 创建缺失的索引
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at DESC);
```

### 安全配置清单

#### 1. 修改默认密码

- [ ] PostgreSQL 密码
- [ ] Redis 密码
- [ ] N8N 管理员密码
- [ ] 应用 SECRET_KEY

#### 2. 配置防火墙

```bash
# 只开放必要端口
sudo ufw allow 22/tcp      # SSH
sudo ufw allow 443/tcp     # HTTPS
sudo ufw enable
```

#### 3. SSL/HTTPS 配置

参考 [Nginx 配置](#nginx-反向代理) 部分。

#### 4. 安全加固

- [ ] 禁用 root 登录
- [ ] 配置 fail2ban
- [ ] 定期更新系统
- [ ] 配置日志审计

---

## 🐳 Docker 部署步骤

### Docker Compose 配置

#### 生产环境配置文件

创建 `docker-compose.prod.yml`：

```yaml
version: '3.8'

services:
  # PostgreSQL 数据库
  postgres:
    image: postgres:15-alpine
    container_name: agentforge-postgres
    environment:
      POSTGRES_DB: agentforge
      POSTGRES_USER: agentforge
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./docker/init-db:/docker-entrypoint-initdb.d
    networks:
      - agentforge-network
    restart: always
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U agentforge"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis 缓存
  redis:
    image: redis:7-alpine
    container_name: agentforge-redis
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    networks:
      - agentforge-network
    restart: always
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Qdrant 向量数据库
  qdrant:
    image: qdrant/qdrant:latest
    container_name: agentforge-qdrant
    volumes:
      - qdrant_data:/qdrant/storage
    networks:
      - agentforge-network
    restart: always

  # N8N 工作流引擎
  n8n:
    image: n8nio/n8n:latest
    container_name: agentforge-n8n
    environment:
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=${N8N_BASIC_AUTH_USER}
      - N8N_BASIC_AUTH_PASSWORD=${N8N_BASIC_AUTH_PASSWORD}
      - N8N_HOST=${PUBLIC_DOMAIN}
      - WEBHOOK_URL=${WEBHOOK_URL}
    volumes:
      - n8n_data:/home/node/.n8n
    networks:
      - agentforge-network
    restart: always

  # 后端应用
  backend:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: agentforge-backend
    env_file:
      - .env.production
    volumes:
      - ./logs:/app/logs
    networks:
      - agentforge-network
    restart: always
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy

  # 前端应用
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: agentforge-frontend
    networks:
      - agentforge-network
    restart: always
    depends_on:
      - backend

  # Nginx 反向代理
  nginx:
    image: nginx:alpine
    container_name: agentforge-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./docker/nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./docker/nginx/ssl:/etc/nginx/ssl
    networks:
      - agentforge-network
    restart: always
    depends_on:
      - frontend
      - backend

volumes:
  postgres_data:
  redis_data:
  qdrant_data:
  n8n_data:

networks:
  agentforge-network:
    driver: bridge
```

### 服务启动和停止

#### 启动所有服务

```bash
# 使用生产配置启动
docker-compose -f docker-compose.prod.yml up -d

# 查看启动日志
docker-compose -f docker-compose.prod.yml logs -f
```

#### 停止所有服务

```bash
# 优雅停止
docker-compose -f docker-compose.prod.yml down

# 强制停止
docker-compose -f docker-compose.prod.yml down -t 30
```

#### 重启服务

```bash
# 重启所有服务
docker-compose -f docker-compose.prod.yml restart

# 重启单个服务
docker-compose -f docker-compose.prod.yml restart backend
```

#### 查看服务状态

```bash
# 查看所有服务状态
docker-compose -f docker-compose.prod.yml ps

# 查看单个服务状态
docker-compose -f docker-compose.prod.yml ps backend
```

### 数据持久化

#### 数据卷位置

```bash
# 查看数据卷
docker volume ls | grep agentforge

# 查看数据卷详情
docker volume inspect agentforge_postgres_data
```

#### 备份数据卷

```bash
# 备份 PostgreSQL 数据
docker run --rm \
  -v agentforge_postgres_data:/var/lib/postgresql/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/postgres_backup.tar.gz /var/lib/postgresql/data

# 备份 Redis 数据
docker run --rm \
  -v agentforge_redis_data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/redis_backup.tar.gz /data
```

### 日志查看

```bash
# 查看所有服务日志
docker-compose -f docker-compose.prod.yml logs -f

# 查看特定服务日志
docker-compose -f docker-compose.prod.yml logs -f backend

# 查看最近 100 行
docker-compose -f docker-compose.prod.yml logs --tail=100 backend

# 导出日志
docker-compose -f docker-compose.prod.yml logs backend > backend.log
```

---

## 📊 监控配置

### Prometheus 配置

#### 安装 Prometheus

```bash
# 创建 Prometheus 配置目录
mkdir -p monitoring/prometheus
```

创建 `monitoring/prometheus/prometheus.yml`：

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

rule_files:
  - "alerts.yml"

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'agentforge'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']

  - job_name: 'nginx'
    static_configs:
      - targets: ['nginx-exporter:9113']
```

#### 配置 Docker Compose

在 `docker-compose.prod.yml` 中添加：

```yaml
  # Prometheus
  prometheus:
    image: prom/prometheus:latest
    container_name: agentforge-prometheus
    volumes:
      - ./monitoring/prometheus:/etc/prometheus
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
    ports:
      - "9090:9090"
    networks:
      - agentforge-network
    restart: always

  # Grafana
  grafana:
    image: grafana/grafana:latest
    container_name: agentforge-grafana
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana:/etc/grafana/provisioning
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
    ports:
      - "3000:3000"
    networks:
      - agentforge-network
    restart: always
    depends_on:
      - prometheus
```

### Grafana 仪表板配置

#### 创建数据源配置

创建 `monitoring/grafana/datasources/prometheus.yml`：

```yaml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true
```

#### 导入仪表板

访问 http://your-domain.com:3000，导入以下仪表板：

1. **系统监控**: Node Exporter Full (ID: 1860)
2. **PostgreSQL 监控**: PostgreSQL Database (ID: 9628)
3. **Redis 监控**: Redis Dashboard (ID: 763)
4. **应用监控**: 自定义仪表板

### 告警规则配置

创建 `monitoring/prometheus/alerts.yml`：

```yaml
groups:
  - name: agentforge_alerts
    rules:
      # 服务宕机告警
      - alert: ServiceDown
        expr: up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "服务 {{ $labels.job }} 宕机"
          description: "{{ $labels.job }} 服务已宕机超过 1 分钟"

      # 高 CPU 使用率
      - alert: HighCPUUsage
        expr: process_cpu_seconds_total > 0.8
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "高 CPU 使用率"
          description: "CPU 使用率超过 80%"

      # 高内存使用率
      - alert: HighMemoryUsage
        expr: process_resident_memory_bytes / 1073741824 > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "高内存使用率"
          description: "内存使用超过 2GB"

      # 数据库连接失败
      - alert: DatabaseConnectionFailed
        expr: pg_up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "数据库连接失败"
          description: "PostgreSQL 数据库无法连接"

      # 错误率过高
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "错误率过高"
          description: "5xx 错误率超过 10%"
```

### 日志聚合

#### 配置 Loki

创建 `monitoring/loki/loki-config.yml`：

```yaml
auth_enabled: false

server:
  http_listen_port: 3100

common:
  path_prefix: /loki
  storage:
    filesystem:
      chunks_directory: /loki/chunks
      rules_directory: /loki/rules
  replication_factor: 1
  ring:
    instance_addr: 127.0.0.1
    kvstore:
      store: inmemory

schema_config:
  configs:
    - from: 2020-10-24
      store: boltdb-shipper
      object_store: filesystem
      schema: v11
      index:
        prefix: index_
        period: 24h

ruler:
  alertmanager_url: http://localhost:9093
```

#### 配置 Promtail

创建 `monitoring/promtail/config.yml`：

```yaml
server:
  http_listen_port: 9080
  grpc_listen_port: 0

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
  - job_name: containers
    static_configs:
      - targets:
          - localhost
        labels:
          job: containerlogs
          __path__: /var/lib/docker/containers/*/*log

    pipeline_stages:
      - json:
          expressions:
            output: log
            stream: stream
            attrs:
      - json:
          expressions:
            tag:
          source: attrs
      - regex:
          expression: (?P<container_name>(?:|(?:[^|]*[^|]))\|)
          source: tag
      - labels:
          - container_name
          - stream
```

---

## 💾 备份和恢复流程

### 数据库备份

#### 自动备份脚本

创建 `scripts/backup_db.sh`：

```bash
#!/bin/bash

# 配置
BACKUP_DIR="/backups/postgres"
DATE=$(date +%Y%m%d_%H%M%S)
CONTAINER_NAME="agentforge-postgres"
DB_NAME="agentforge"
DB_USER="agentforge"
RETENTION_DAYS=30

# 创建备份目录
mkdir -p $BACKUP_DIR

# 执行备份
echo "开始备份数据库..."
docker exec $CONTAINER_NAME pg_dump -U $DB_USER $DB_NAME | gzip > $BACKUP_DIR/backup_$DATE.sql.gz

# 检查备份是否成功
if [ $? -eq 0 ]; then
    echo "备份成功：$BACKUP_DIR/backup_$DATE.sql.gz"
    
    # 删除过期备份
    echo "清理过期备份..."
    find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +$RETENTION_DAYS -delete
    
    echo "备份完成"
else
    echo "备份失败"
    exit 1
fi
```

#### 配置定时任务

```bash
# 编辑 crontab
crontab -e

# 添加每天凌晨 2 点备份
0 2 * * * /path/to/scripts/backup_db.sh >> /var/log/backup.log 2>&1
```

### 文件备份

#### 备份脚本

创建 `scripts/backup_files.sh`：

```bash
#!/bin/bash

# 配置
BACKUP_DIR="/backups/files"
DATE=$(date +%Y%m%d_%H%M%S)
SOURCE_DIRS=(
    "/path/to/agentforge/logs"
    "/path/to/agentforge/.env.production"
    "/path/to/agentforge/docker"
)
RETENTION_DAYS=30

# 创建备份目录
mkdir -p $BACKUP_DIR

# 压缩备份
echo "开始备份文件..."
tar -czf $BACKUP_DIR/files_backup_$DATE.tar.gz "${SOURCE_DIRS[@]}"

# 检查备份
if [ $? -eq 0 ]; then
    echo "文件备份成功：$BACKUP_DIR/files_backup_$DATE.tar.gz"
    
    # 清理过期备份
    find $BACKUP_DIR -name "files_backup_*.tar.gz" -mtime +$RETENTION_DAYS -delete
    
    echo "文件备份完成"
else
    echo "文件备份失败"
    exit 1
fi
```

### 数据恢复

#### 恢复数据库

```bash
#!/bin/bash

# 配置
BACKUP_FILE=$1
CONTAINER_NAME="agentforge-postgres"
DB_NAME="agentforge"
DB_USER="agentforge"

# 检查备份文件
if [ ! -f "$BACKUP_FILE" ]; then
    echo "备份文件不存在：$BACKUP_FILE"
    exit 1
fi

# 恢复数据库
echo "开始恢复数据库..."
gunzip -c $BACKUP_FILE | docker exec -i $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME

if [ $? -eq 0 ]; then
    echo "数据库恢复成功"
else
    echo "数据库恢复失败"
    exit 1
fi
```

#### 恢复文件

```bash
#!/bin/bash

# 配置
BACKUP_FILE=$1
TARGET_DIR=$2

# 检查备份文件
if [ ! -f "$BACKUP_FILE" ]; then
    echo "备份文件不存在：$BACKUP_FILE"
    exit 1
fi

# 恢复文件
echo "开始恢复文件..."
tar -xzf $BACKUP_FILE -C $TARGET_DIR

if [ $? -eq 0 ]; then
    echo "文件恢复成功"
else
    echo "文件恢复失败"
    exit 1
fi
```

### 灾难恢复流程

#### 1. 评估损失

- 确定哪些数据丢失
- 确定最后一次成功备份时间
- 评估恢复优先级

#### 2. 准备恢复环境

```bash
# 停止所有服务
docker-compose -f docker-compose.prod.yml down

# 清理损坏的数据卷
docker volume rm agentforge_postgres_data

# 重新创建数据卷
docker-compose -f docker-compose.prod.yml up -d postgres
```

#### 3. 恢复数据

```bash
# 恢复数据库
./scripts/restore_db.sh /backups/postgres/backup_20260330_020000.sql.gz

# 恢复文件
./scripts/restore_files.sh /backups/files/files_backup_20260330_020000.tar.gz /path/to/agentforge
```

#### 4. 验证恢复

```bash
# 检查数据库连接
docker-compose exec postgres psql -U agentforge -d agentforge -c "SELECT COUNT(*) FROM tasks;"

# 检查应用日志
docker-compose logs backend | tail -100

# 测试 API 端点
curl http://localhost:8000/api/health
```

#### 5. 恢复服务

```bash
# 启动所有服务
docker-compose -f docker-compose.prod.yml up -d

# 监控服务状态
watch docker-compose -f docker-compose.prod.yml ps
```

#### 6. 事后总结

- 记录灾难原因
- 评估恢复时间
- 改进备份策略
- 更新恢复流程

---

## 📚 相关文档

- [用户手册](USER_GUIDE.md) - 用户使用指南
- [架构文档](architecture/adr.md) - 架构决策记录
- [API 文档](http://localhost:8000/docs) - Swagger UI

---

**最后更新**: 2026-03-30  
**版本**: 1.0.0
