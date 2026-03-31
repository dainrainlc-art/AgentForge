# AgentForge Docker 部署文档

本文档详细说明AgentForge系统的Docker部署流程、环境变量配置、数据持久化和故障排除方法。

## 1. Docker部署流程

### 1.1 系统要求

| 项目 | 最低要求 | 推荐配置 |
|------|----------|----------|
| Docker | 24.0+ | 最新稳定版 |
| Docker Compose | 2.20+ | 最新稳定版 |
| 内存 | 8GB | 16GB+ |
| CPU | 4核 | 8核+ |
| 存储 | 50GB | 100GB+ SSD |

### 1.2 前置条件

#### 1.2.1 安装Docker

**Windows/macOS**:
```bash
# 下载并安装 Docker Desktop
# https://www.docker.com/products/docker-desktop

# 验证安装
docker --version
docker-compose --version
```

**Linux (Ubuntu)**:
```bash
# 安装Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 添加当前用户到docker组
sudo usermod -aG docker $USER

# 安装Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 验证安装
docker --version
docker-compose --version
```

#### 1.2.2 克隆项目

```bash
git clone https://github.com/your-username/AgentForge.git
cd AgentForge
```

### 1.3 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑配置文件
nano .env
```

### 1.4 启动服务

#### 1.4.1 使用启动脚本

```bash
# 启动所有服务
./start-services.sh

# 或使用deploy脚本
./deploy.sh
```

#### 1.4.2 手动启动

```bash
# 构建并启动所有服务
docker-compose up -d --build

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

#### 1.4.3 分步启动

```bash
# 先启动数据存储层
docker-compose up -d postgres redis qdrant

# 等待数据库就绪
sleep 10

# 启动N8N工作流引擎
docker-compose up -d n8n

# 启动AgentForge核心服务
docker-compose up -d agentforge-core
```

### 1.5 验证部署

访问以下地址验证服务状态：

| 服务 | 地址 | 说明 |
|------|------|------|
| AgentForge API | http://localhost:8000 | API服务 |
| API文档 | http://localhost:8000/docs | Swagger UI |
| N8N工作流 | http://localhost:5678 | 工作流编辑器 |
| Qdrant控制台 | http://localhost:6333/dashboard | 向量数据库 |
| PostgreSQL | localhost:5432 | 数据库 |
| Redis | localhost:6379 | 缓存服务 |

## 2. 环境变量配置

### 2.1 核心配置

```env
# ==================== 核心配置 ====================

# 应用环境 (development/production)
APP_ENV=development

# 时区设置
TZ=Asia/Shanghai

# 日志级别 (DEBUG/INFO/WARNING/ERROR)
LOG_LEVEL=INFO
```

### 2.2 百度千帆API配置

```env
# ==================== 百度千帆配置 ====================

# 百度千帆API Key (必填)
QIANFAN_API_KEY=your_api_key_here

# 默认模型
LLM_MODEL=glm-5

# 备选模型列表
LLM_FALLBACK_MODELS=deepseek-v3.2,kimi-k2.5,minimax-m2.5
```

### 2.3 数据库配置

```env
# ==================== PostgreSQL配置 ====================

POSTGRES_USER=agentforge
POSTGRES_PASSWORD=your_secure_password_here
POSTGRES_DB=agentforge
POSTGRES_PORT=5432

# 数据库连接URL
DATABASE_URL=postgresql://agentforge:your_secure_password_here@postgres:5432/agentforge
```

### 2.4 Redis配置

```env
# ==================== Redis配置 ====================

REDIS_PORT=6379
REDIS_URL=redis://redis:6379

# Redis密码 (可选)
# REDIS_PASSWORD=your_redis_password
```

### 2.5 Qdrant配置

```env
# ==================== Qdrant配置 ====================

QDRANT_URL=http://qdrant:6333
QDRANT_API_KEY=  # 可选
```

### 2.6 N8N配置

```env
# ==================== N8N配置 ====================

N8N_PORT=5678
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=your_n8n_password
N8N_WEBHOOK_URL=http://localhost:5678/webhook/
```

### 2.7 安全配置

```env
# ==================== 安全配置 ====================

# JWT密钥 (必填，至少32字符)
SECRET_KEY=your_secret_key_at_least_32_characters_long

# 数据加密密钥 (必填，32字符)
ENCRYPTION_KEY=your_32_character_encryption_key

# JWT过期时间 (秒)
JWT_EXPIRATION=3600

# 刷新令牌过期时间 (秒)
REFRESH_TOKEN_EXPIRATION=604800
```

### 2.8 Obsidian集成配置

```env
# ==================== Obsidian配置 ====================

# Obsidian库路径
OBSIDIAN_VAULT_PATH=/path/to/your/obsidian/vault
```

### 2.9 完整配置示例

```env
# ==================== AgentForge 环境配置 ====================
# 复制此文件为 .env 并填写必要配置

# 核心配置
APP_ENV=development
TZ=Asia/Shanghai
LOG_LEVEL=INFO

# 百度千帆API
QIANFAN_API_KEY=your_qianfan_api_key
LLM_MODEL=glm-5
LLM_FALLBACK_MODELS=deepseek-v3.2,kimi-k2.5,minimax-m2.5

# PostgreSQL
POSTGRES_USER=agentforge
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=agentforge
POSTGRES_PORT=5432

# Redis
REDIS_PORT=6379

# Qdrant
QDRANT_URL=http://qdrant:6333

# N8N
N8N_PORT=5678
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=your_n8n_password

# 安全
SECRET_KEY=your_secret_key_at_least_32_characters_long
ENCRYPTION_KEY=your_32_character_encryption_key

# Obsidian (可选)
OBSIDIAN_VAULT_PATH=/path/to/vault
```

## 3. 数据持久化

### 3.1 Docker卷管理

AgentForge使用Docker卷进行数据持久化：

```yaml
volumes:
  postgres-data:    # PostgreSQL数据
    driver: local
  redis-data:       # Redis数据
    driver: local
  qdrant-data:      # Qdrant向量数据
    driver: local
```

### 3.2 数据存储位置

| 服务 | 容器路径 | 宿主机路径 |
|------|----------|------------|
| PostgreSQL | /var/lib/postgresql/data | Docker卷: postgres-data |
| Redis | /data | Docker卷: redis-data |
| Qdrant | /qdrant/storage | Docker卷: qdrant-data |
| N8N | /home/node/.n8n | ./workflows |
| AgentForge | /app/data | ./data |

### 3.3 数据备份

#### 3.3.1 PostgreSQL备份

```bash
# 创建备份
docker-compose exec postgres pg_dump -U agentforge agentforge > backup_$(date +%Y%m%d).sql

# 恢复备份
cat backup_20260326.sql | docker-compose exec -T postgres psql -U agentforge agentforge
```

#### 3.3.2 Redis备份

```bash
# 触发RDB快照
docker-compose exec redis redis-cli BGSAVE

# 复制备份文件
docker cp agentforge-redis:/data/dump.rdb ./backup/redis_$(date +%Y%m%d).rdb
```

#### 3.3.3 Qdrant备份

```bash
# 创建快照
curl -X POST http://localhost:6333/collections/agentforge/snapshots

# 下载快照
curl http://localhost:6333/collections/agentforge/snapshots/snapshot_name -o snapshot.tar
```

#### 3.3.4 完整备份脚本

```bash
#!/bin/bash
# backup.sh - AgentForge完整备份脚本

BACKUP_DIR="./backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR

# PostgreSQL备份
docker-compose exec -T postgres pg_dump -U agentforge agentforge > $BACKUP_DIR/postgres.sql

# Redis备份
docker-compose exec redis redis-cli BGSAVE
sleep 2
docker cp agentforge-redis:/data/dump.rdb $BACKUP_DIR/redis.rdb

# Qdrant备份
curl -s -X POST http://localhost:6333/collections/agentforge/snapshots

# 打包
tar -czf $BACKUP_DIR.tar.gz $BACKUP_DIR
rm -rf $BACKUP_DIR

echo "Backup completed: $BACKUP_DIR.tar.gz"
```

### 3.4 数据恢复

```bash
# 恢复PostgreSQL
cat backup/postgres.sql | docker-compose exec -T postgres psql -U agentforge agentforge

# 恢复Redis
docker cp backup/redis.rdb agentforge-redis:/data/dump.rdb
docker-compose restart redis

# 恢复Qdrant
curl -X PUT http://localhost:6333/collections/agentforge/snapshots/recover \
  -H "Content-Type: multipart/form-data" \
  -F "snapshot=@snapshot.tar"
```

## 4. 故障排除

### 4.1 常见问题

#### 4.1.1 服务无法启动

**症状**：`docker-compose up` 失败

**排查步骤**：
```bash
# 检查Docker服务状态
systemctl status docker

# 检查端口占用
netstat -tlnp | grep -E '8000|5432|6379|6333|5678'

# 查看详细错误日志
docker-compose up --no-start
docker-compose logs
```

**解决方案**：
- 确保端口未被占用
- 检查环境变量配置
- 确保有足够的磁盘空间

#### 4.1.2 数据库连接失败

**症状**：`Connection refused` 或 `FATAL: password authentication failed`

**排查步骤**：
```bash
# 检查PostgreSQL状态
docker-compose ps postgres
docker-compose logs postgres

# 测试连接
docker-compose exec postgres psql -U agentforge -d agentforge
```

**解决方案**：
```bash
# 重置数据库
docker-compose down -v
docker-compose up -d postgres

# 检查密码配置
grep POSTGRES_PASSWORD .env
```

#### 4.1.3 内存不足

**症状**：服务频繁重启，OOM错误

**排查步骤**：
```bash
# 查看容器资源使用
docker stats

# 查看系统内存
free -h
```

**解决方案**：
```yaml
# 在docker-compose.yml中添加资源限制
services:
  agentforge-core:
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G
```

#### 4.1.4 API响应超时

**症状**：请求长时间无响应

**排查步骤**：
```bash
# 检查服务健康状态
curl http://localhost:8000/health

# 检查日志
docker-compose logs -f agentforge-core

# 检查LLM服务状态
curl -I https://qianfan.baidubce.com
```

**解决方案**：
- 检查百度千帆API Key是否有效
- 检查网络连接
- 检查请求频率是否超限

### 4.2 日志查看

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f agentforge-core
docker-compose logs -f postgres
docker-compose logs -f n8n

# 查看最近100行日志
docker-compose logs --tail=100 agentforge-core

# 过滤日志
docker-compose logs agentforge-core | grep ERROR
```

### 4.3 服务管理命令

```bash
# 启动服务
docker-compose up -d

# 停止服务
docker-compose down

# 重启特定服务
docker-compose restart agentforge-core

# 重建服务
docker-compose up -d --build agentforge-core

# 进入容器
docker-compose exec agentforge-core bash

# 查看容器状态
docker-compose ps

# 查看资源使用
docker stats
```

### 4.4 健康检查

```bash
# 检查所有服务健康状态
./health-check.sh
```

**health-check.sh**:
```bash
#!/bin/bash

services=(
  "AgentForge API|http://localhost:8000/health"
  "N8N|http://localhost:5678/healthz"
  "Qdrant|http://localhost:6333/collections"
  "PostgreSQL|localhost:5432"
  "Redis|localhost:6379"
)

echo "=== AgentForge Health Check ==="

for service in "${services[@]}"; do
  IFS='|' read -r name url <<< "$service"
  echo -n "Checking $name... "
  
  if curl -s -o /dev/null -w "%{http_code}" "$url" | grep -q "200"; then
    echo "✓ OK"
  else
    echo "✗ FAILED"
  fi
done
```

### 4.5 性能调优

#### 4.5.1 PostgreSQL优化

```sql
-- 在容器内执行
docker-compose exec postgres psql -U agentforge -d agentforge

-- 创建索引
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_created_at ON orders(created_at);

-- 分析表
ANALYZE orders;
```

#### 4.5.2 Redis优化

```bash
# 设置最大内存
docker-compose exec redis redis-cli CONFIG SET maxmemory 1gb

# 设置淘汰策略
docker-compose exec redis redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

#### 4.5.3 Docker优化

```yaml
# docker-compose.yml
services:
  agentforge-core:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
    ulimits:
      nofile:
        soft: 65536
        hard: 65536
```

## 5. 生产环境部署

### 5.1 生产环境配置

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  agentforge-core:
    build:
      context: .
      dockerfile: docker/Dockerfile.agentforge
    restart: always
    environment:
      - APP_ENV=production
      - LOG_LEVEL=WARNING
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 4G
      replicas: 2
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### 5.2 启动生产环境

```bash
docker-compose -f docker-compose.prod.yml up -d
```

### 5.3 安全加固

1. **使用HTTPS**：配置反向代理（Nginx/Traefik）
2. **限制端口暴露**：仅暴露必要端口
3. **使用密钥管理**：使用Docker Secrets或Vault
4. **定期更新**：保持镜像和依赖更新

## 6. 相关文档

- [架构概览](../architecture/overview.md)
- [部署架构设计](../architecture/deployment-architecture.md)
- [开发指南](../guides/development.md)
