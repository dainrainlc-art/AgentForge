# AgentForge 部署架构设计

## 1. Docker部署架构

### 1.1 容器编排方案

```yaml
# docker-compose.yml 完整配置
version: '3.8'

services:
  # ===========================================
  # 核心服务
  # ===========================================
  
  agentforge-core:
    build:
      context: .
      dockerfile: docker/Dockerfile.agentforge
    container_name: agentforge-core
    hostname: agentforge-core
    ports:
      - "8080:8080"    # HTTP API
      - "8081:8081"    # WebSocket
    volumes:
      - ./data:/app/data
      - ./.trae:/app/.trae
      - ${OBSIDIAN_VAULT_PATH:-./vault}:/vault:ro
    environment:
      - LLM_PROVIDER=qianfan
      - QIANFAN_API_KEY=${QIANFAN_API_KEY}
      - LLM_MODEL=glm-5
      - LLM_FALLBACK_MODELS=deepseek-v3.2,kimi-k2.5,minimax-m2.5
      - DATABASE_URL=postgresql://${POSTGRES_USER:-agentforge}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB:-agentforge}
      - REDIS_URL=redis://redis:6379
      - QDRANT_URL=http://qdrant:6333
      - N8N_WEBHOOK_URL=http://n8n:5678/webhook/
      - TZ=${TZ:-Asia/Shanghai}
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_started
      qdrant:
        condition: service_started
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    restart: unless-stopped
    networks:
      - agentforge-network
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M

  # ===========================================
  # 工作流引擎
  # ===========================================
  
  n8n:
    image: n8nio/n8n:latest
    container_name: agentforge-n8n
    hostname: n8n
    ports:
      - "${N8N_PORT:-5678}:5678"
    volumes:
      - ./workflows:/home/node/.n8n
      - ./data/n8n:/data
    environment:
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=${N8N_BASIC_AUTH_USER:-admin}
      - N8N_BASIC_AUTH_PASSWORD=${N8N_BASIC_AUTH_PASSWORD}
      - WEBHOOK_URL=${N8N_WEBHOOK_URL:-http://localhost:5678/webhook/}
      - EXECUTIONS_MODE=regular
      - EXECUTIONS_TIMEOUT=600
      - EXECUTIONS_TIMEOUT_MAX=3600
      - GENERIC_TIMEZONE=${TZ:-Asia/Shanghai}
      - N8N_LOG_LEVEL=${LOG_LEVEL:-info}
      - N8N_METRICS=true
    healthcheck:
      test: ["CMD", "wget", "-q", "--spider", "http://localhost:5678/healthz"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped
    networks:
      - agentforge-network
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G

  # ===========================================
  # 数据存储
  # ===========================================
  
  postgres:
    image: postgres:15-alpine
    container_name: agentforge-postgres
    hostname: postgres
    ports:
      - "${POSTGRES_PORT:-5432}:5432"
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./docker/init-db:/docker-entrypoint-initdb.d
    environment:
      - POSTGRES_DB=${POSTGRES_DB:-agentforge}
      - POSTGRES_USER=${POSTGRES_USER:-agentforge}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - PGDATA=/var/lib/postgresql/data/pgdata
      - TZ=${TZ:-Asia/Shanghai}
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-agentforge} -d ${POSTGRES_DB:-agentforge}"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s
    restart: unless-stopped
    networks:
      - agentforge-network
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G

  redis:
    image: redis:7-alpine
    container_name: agentforge-redis
    hostname: redis
    ports:
      - "${REDIS_PORT:-6379}:6379"
    volumes:
      - redis-data:/data
    command: >
      redis-server
      --appendonly yes
      --maxmemory 256mb
      --maxmemory-policy allkeys-lru
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 3
    restart: unless-stopped
    networks:
      - agentforge-network
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M

  qdrant:
    image: qdrant/qdrant:latest
    container_name: agentforge-qdrant
    hostname: qdrant
    ports:
      - "6333:6333"    # HTTP API
      - "6334:6334"    # gRPC API
    volumes:
      - qdrant-data:/qdrant/storage
    environment:
      - QDRANT__LOG_LEVEL=${LOG_LEVEL:-INFO}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:6333/"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped
    networks:
      - agentforge-network
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G

volumes:
  postgres-data:
    driver: local
  redis-data:
    driver: local
  qdrant-data:
    driver: local

networks:
  agentforge-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.28.0.0/16
```

### 1.2 网络配置方案

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Docker网络架构                                      │
└─────────────────────────────────────────────────────────────────────────────┘

                    外部访问
                        │
                        │ localhost:8080
                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      agentforge-network (Bridge)                             │
│                         172.28.0.0/16                                        │
│                                                                              │
│   ┌─────────────────┐                                                        │
│   │ agentforge-core │ 172.28.0.10                                            │
│   │   :8080/:8081   │                                                        │
│   └────────┬────────┘                                                        │
│            │                                                                 │
│   ┌────────┴────────┬─────────────────┬─────────────────┐                   │
│   │                 │                 │                 │                   │
│   ▼                 ▼                 ▼                 ▼                   │
│ ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐                      │
│ │  n8n     │  │ postgres │  │  redis   │  │  qdrant  │                      │
│ │ :5678    │  │ :5432    │  │ :6379    │  │ :6333    │                      │
│ │ 172.28.  │  │ 172.28.  │  │ 172.28.  │  │ 172.28.  │                      │
│ │ 0.20     │  │ 0.30     │  │ 0.40     │  │ 0.50     │                      │
│ └──────────┘  └──────────┘  └──────────┘  └──────────┘                      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

**网络隔离策略**:
- 所有服务在同一Docker网络内
- 仅暴露必要端口到主机
- 内部服务间通过容器名访问

### 1.3 存储卷管理方案

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          存储卷架构                                          │
└─────────────────────────────────────────────────────────────────────────────┘

主机文件系统
│
├── /var/lib/docker/volumes/
│   ├── agentforge_postgres-data/    # PostgreSQL数据
│   │   └── _data/
│   │       └── pgdata/
│   │
│   ├── agentforge_redis-data/       # Redis数据
│   │   └── _data/
│   │       └── appendonly.aof
│   │
│   └── agentforge_qdrant-data/      # Qdrant数据
│       └── _data/
│           └── collections/
│
└── /home/dainrain4/trae_projects/AgentForge/
    ├── data/                        # 应用数据
    │   ├── n8n/                    # N8N数据
    │   └── exports/                # 导出文件
    │
    ├── workflows/                   # N8N工作流
    │
    └── vault/                       # Obsidian知识库 (挂载)
```

**备份策略**:
```bash
# 每日备份脚本
#!/bin/bash
BACKUP_DIR="/backup/agentforge/$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR

# PostgreSQL备份
docker exec agentforge-postgres pg_dump -U agentforge agentforge > $BACKUP_DIR/postgres.sql

# Redis备份
docker exec agentforge-redis redis-cli BGSAVE
docker cp agentforge-redis:/data/dump.rdb $BACKUP_DIR/redis.rdb

# Qdrant备份
curl -X POST http://localhost:6333/collections/*/snapshots

# 压缩备份
tar -czf $BACKUP_DIR.tar.gz $BACKUP_DIR
rm -rf $BACKUP_DIR
```

### 1.4 容器健康检查方案

**健康检查配置**:
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
  interval: 30s      # 检查间隔
  timeout: 10s       # 超时时间
  retries: 3         # 重试次数
  start_period: 40s  # 启动等待时间
```

**健康检查端点**:
```python
@app.get("/health")
async def health_check():
    """健康检查端点"""
    checks = {
        "database": await check_database(),
        "redis": await check_redis(),
        "qdrant": await check_qdrant(),
        "llm": await check_llm_connection()
    }
    
    all_healthy = all(checks.values())
    
    return {
        "status": "healthy" if all_healthy else "unhealthy",
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat()
    }
```

## 2. 运维监控架构

### 2.1 日志聚合方案

**日志架构**:
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          日志聚合架构                                        │
└─────────────────────────────────────────────────────────────────────────────┘

各容器应用日志
    │
    │ stdout/stderr
    ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                          Docker Logging Driver                                │
│                                                                              │
│   json-file (默认)                                                           │
│   ├── /var/lib/docker/containers/<id>/<id>-json.log                         │
│   └── 日志轮转: max-size=10m, max-file=3                                    │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
    │
    │ 日志采集
    ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                          日志处理                                            │
│                                                                              │
│   ├── 结构化日志 (JSON格式)                                                  │
│   ├── 日志级别过滤                                                          │
│   ├── 敏感信息脱敏                                                          │
│   └── 日志聚合                                                              │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
    │
    │ 存储
    ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                          日志存储                                            │
│                                                                              │
│   PostgreSQL (activity_logs表)                                               │
│   ├── 操作日志                                                              │
│   ├── 审计日志                                                              │
│   └── 保留期限: 90天                                                        │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

**日志格式**:
```python
LOG_FORMAT = {
    "timestamp": "2026-03-26T10:00:00Z",
    "level": "INFO",
    "logger": "agentforge.core",
    "message": "Order processed successfully",
    "context": {
        "request_id": "uuid",
        "user_id": "user_123",
        "order_id": "order_456"
    },
    "extra": {}
}
```

### 2.2 性能监控方案

**监控指标**:
```python
METRICS = {
    # 系统指标
    "system": {
        "cpu_usage": "CPU使用率",
        "memory_usage": "内存使用率",
        "disk_usage": "磁盘使用率",
        "network_io": "网络IO"
    },
    
    # 应用指标
    "application": {
        "request_count": "请求计数",
        "request_latency": "请求延迟",
        "error_rate": "错误率",
        "active_connections": "活跃连接数"
    },
    
    # 业务指标
    "business": {
        "orders_processed": "处理订单数",
        "content_generated": "生成内容数",
        "llm_calls": "LLM调用次数",
        "api_quota_used": "API配额使用"
    },
    
    # 数据库指标
    "database": {
        "connections": "连接数",
        "query_latency": "查询延迟",
        "slow_queries": "慢查询数",
        "cache_hit_rate": "缓存命中率"
    }
}
```

**监控仪表板**:
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          AgentForge 监控仪表板                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  系统状态                    │  应用性能                                     │
│  ┌─────────────────────────┐ │ ┌─────────────────────────┐                  │
│  │ CPU:     45% ████████░░ │ │ │ 请求/秒:  120           │                  │
│  │ 内存:    60% ██████████ │ │ │ 平均延迟: 85ms          │                  │
│  │ 磁盘:    35% ██████░░░░ │ │ │ 错误率:   0.5%          │                  │
│  └─────────────────────────┘ │ └─────────────────────────┘                  │
│                              │                                               │
│  API配额                     │  业务统计                                     │
│  ┌─────────────────────────┐ │ ┌─────────────────────────┐                  │
│  │ 今日:  2,340 / 6,000    │ │ │ 订单: 15 (今日)         │                  │
│  │ 本周:  12,500 / 45,000  │ │ │ 内容: 23 (今日)         │                  │
│  │ 本月:  45,000 / 90,000  │ │ │ 消息: 67 (今日)         │                  │
│  └─────────────────────────┘ │ └─────────────────────────┘                  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.3 告警通知方案

**告警规则配置**:
```python
ALERT_RULES = {
    "high_cpu": {
        "metric": "cpu_usage",
        "threshold": 80,
        "duration": "5m",
        "severity": "warning",
        "message": "CPU使用率超过80%"
    },
    "high_memory": {
        "metric": "memory_usage",
        "threshold": 85,
        "duration": "5m",
        "severity": "warning",
        "message": "内存使用率超过85%"
    },
    "api_quota_critical": {
        "metric": "api_quota_remaining",
        "threshold": 1000,
        "severity": "critical",
        "message": "API配额即将耗尽"
    },
    "service_down": {
        "metric": "service_health",
        "condition": "unhealthy",
        "severity": "critical",
        "message": "服务不可用"
    }
}
```

**通知渠道**:
```python
NOTIFICATION_CHANNELS = {
    "desktop": {
        "type": "desktop_notification",
        "enabled": True,
        "severity": ["warning", "critical"]
    },
    "telegram": {
        "type": "telegram_bot",
        "chat_id": "${TELEGRAM_CHAT_ID}",
        "enabled": True,
        "severity": ["critical"]
    },
    "email": {
        "type": "smtp",
        "recipients": ["admin@example.com"],
        "enabled": False,
        "severity": ["critical"]
    }
}
```

### 2.4 备份恢复方案

**备份计划**:
| 备份类型 | 频率 | 保留期限 | 存储位置 |
|----------|------|----------|----------|
| 全量备份 | 每日 | 30天 | 本地 + 云存储 |
| 增量备份 | 每小时 | 7天 | 本地 |
| 配置备份 | 每次变更 | 永久 | Git仓库 |

**恢复流程**:
```bash
# 1. 停止服务
docker-compose down

# 2. 恢复PostgreSQL
docker volume rm agentforge_postgres-data
docker volume create agentforge_postgres-data
docker run --rm -v agentforge_postgres-data:/data -v /backup:/backup alpine tar -xzf /backup/postgres.tar.gz -C /data

# 3. 恢复Redis
docker run --rm -v agentforge_redis-data:/data -v /backup:/backup alpine cp /backup/redis.rdb /data/

# 4. 启动服务
docker-compose up -d

# 5. 验证恢复
curl http://localhost:8080/health
```

## 3. 资源规划

### 3.1 最低配置要求

| 资源 | 最低要求 | 推荐配置 |
|------|----------|----------|
| CPU | 2核 | 4核+ |
| 内存 | 4GB | 8GB+ |
| 存储 | 50GB SSD | 100GB SSD |
| 网络 | 宽带连接 | 稳定网络 |

### 3.2 容器资源分配

| 容器 | CPU限制 | 内存限制 | CPU预留 | 内存预留 |
|------|---------|----------|---------|----------|
| agentforge-core | 2核 | 2GB | 0.5核 | 512MB |
| n8n | 1核 | 1GB | 0.25核 | 256MB |
| postgres | 1核 | 1GB | 0.25核 | 256MB |
| redis | 0.5核 | 512MB | 0.1核 | 128MB |
| qdrant | 1核 | 1GB | 0.25核 | 256MB |
| **总计** | **5.5核** | **5.5GB** | **1.35核** | **1.4GB** |
