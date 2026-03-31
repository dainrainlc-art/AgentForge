# AgentForge 快速部署指南

> 解决常见问题，快速启动系统

---

## 🔧 问题修复

### 问题 1: Docker 权限错误

**错误信息**:
```
PermissionError: [Errno 13] Permission denied
```

**解决方案**:

将当前用户添加到 Docker 组：

```bash
# 1. 将用户添加到 docker 组
sudo usermod -aG docker $USER

# 2. 重新登录或执行以下命令使更改生效
newgrp docker

# 3. 验证权限
docker ps
```

**临时方案**（不推荐长期使用）:
```bash
sudo docker-compose -f docker-compose.prod.yml up -d
```

---

### 问题 2: 监控服务依赖问题

**错误信息**:
```
Service 'postgres-exporter' depends on service 'postgres' which is undefined
```

**原因**: 监控配置文件中的服务名称与实际不符

**解决方案**:

已修复 `docker-compose.monitoring.yml`，使用 `host.docker.internal` 连接到主机 Docker 服务：

```bash
# 现在可以直接运行
docker-compose -f docker-compose.monitoring.yml up -d
```

---

### 问题 3: 脚本权限不够

**错误信息**:
```
bash: ./scripts/update-ssl-cert.sh: 权限不够
```

**解决方案**:

```bash
# 添加执行权限
chmod +x scripts/update-ssl-cert.sh

# 然后运行
./scripts/update-ssl-cert.sh request
```

---

## 🚀 正确的部署步骤

### 步骤 1: 修复 Docker 权限

```bash
# 添加用户到 docker 组
sudo usermod -aG docker $USER
newgrp docker

# 验证
docker ps
```

### 步骤 2: 启动应用服务

```bash
# 启动主应用
docker-compose -f docker-compose.prod.yml up -d

# 查看状态
docker-compose -f docker-compose.prod.yml ps

# 查看日志
docker-compose -f docker-compose.prod.yml logs -f
```

### 步骤 3: 启动监控系统

```bash
# 启动监控服务
docker-compose -f docker-compose.monitoring.yml up -d

# 查看监控服务状态
docker-compose -f docker-compose.monitoring.yml ps
```

### 步骤 4: 配置 SSL 证书（可选）

```bash
# 添加脚本执行权限
chmod +x scripts/update-ssl-cert.sh

# 设置环境变量
export DOMAIN_NAME=your-domain.com
export ADMIN_EMAIL=admin@example.com

# 申请证书
./scripts/update-ssl-cert.sh request
```

---

## 📋 快速验证清单

### Docker 权限验证

```bash
# 应该能看到容器列表
docker ps

# 应该能看到镜像
docker images
```

### 应用服务验证

```bash
# 检查所有服务是否运行
docker-compose -f docker-compose.prod.yml ps

# 应该看到以下服务：
# - agentforge-api
# - agentforge-frontend
# - postgres
# - redis
# - qdrant
# - n8n
```

### 监控服务验证

```bash
# 检查监控服务
docker-compose -f docker-compose.monitoring.yml ps

# 应该看到以下服务：
# - prometheus
# - grafana
# - alertmanager
# - node-exporter
# - postgres-exporter
# - redis-exporter
# - nginx-exporter
# - loki
# - promtail
```

### 服务访问验证

```bash
# 测试 API 健康检查
curl http://localhost:8000/api/health

# 测试前端
curl http://localhost:80

# 测试 Prometheus
curl http://localhost:9090/-/healthy

# 测试 Grafana
curl http://localhost:3000/api/health
```

---

## 🔍 常见问题排查

### 问题：docker ps 仍然提示权限错误

**解决方案**:
```bash
# 完全退出并重新登录
exit
# 然后重新 SSH 登录或重新打开终端
```

### 问题：服务启动失败

**查看日志**:
```bash
# 查看所有服务日志
docker-compose -f docker-compose.prod.yml logs

# 查看特定服务日志
docker-compose -f docker-compose.prod.yml logs agentforge-api
```

### 问题：端口冲突

**检查端口占用**:
```bash
# 查看端口占用
sudo lsof -i :8000
sudo lsof -i :5432
sudo lsof -i :6379
```

**解决方案**:
```bash
# 停止占用端口的服务
sudo systemctl stop <service>
# 或修改 docker-compose.yml 中的端口映射
```

### 问题：监控系统无法连接到数据库

**解决方案**:
```bash
# 确保 PostgreSQL 允许远程连接
# 编辑 postgresql.conf
# listen_addresses = '*'

# 编辑 pg_hba.conf
# host all all 0.0.0.0/0 md5
```

---

## 📊 服务访问地址

### 应用服务

| 服务 | 地址 | 说明 |
|------|------|------|
| 前端应用 | http://localhost | React 前端 |
| API 服务 | http://localhost:8000 | REST API |
| API 文档 | http://localhost:8000/docs | Swagger UI |
| N8N | http://localhost:5678 | 工作流引擎 |
| Qdrant | http://localhost:6333 | 向量数据库 |

### 监控服务

| 服务 | 地址 | 说明 |
|------|------|------|
| Grafana | http://localhost:3000 | 监控仪表板 |
| Prometheus | http://localhost:9090 | 指标查询 |
| Alertmanager | http://localhost:9093 | 告警管理 |
| Loki | http://localhost:3100 | 日志聚合 |

---

## 🎯 下一步

1. **配置环境变量**
   ```bash
   cp .env.example .env
   # 编辑 .env 文件，填写必要配置
   ```

2. **初始化数据库**
   ```bash
   docker-compose -f docker-compose.prod.yml exec postgres psql -U agentforge -d agentforge -f /docker-entrypoint-initdb.d/01_schema.sql
   ```

3. **访问 Grafana**
   - 地址：http://localhost:3000
   - 账号：admin
   - 密码：admin（首次登录后修改）

4. **导入监控仪表板**
   - 使用 monitoring/grafana/dashboards/agentforge-main.json

---

## 📞 获取帮助

如果遇到问题：

1. 查看日志：`docker-compose logs -f`
2. 检查配置：`docker-compose config`
3. 查看文档：docs/DEPLOYMENT.md
4. 查看实施指南：docs/PHASE3_IMPLEMENTATION_GUIDE.md

---

**最后更新**: 2026-03-30  
**版本**: v1.0.1 (修复版)
