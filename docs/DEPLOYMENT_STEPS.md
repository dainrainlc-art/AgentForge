# AgentForge 部署步骤

## 快速部署（推荐）

使用自动化部署脚本：

```bash
# 添加执行权限
chmod +x scripts/deploy.sh

# 运行部署脚本
./scripts/deploy.sh
```

### 脚本选项

```bash
# 完整部署（构建 + 启动）
./scripts/deploy.sh

# 只构建
./scripts/deploy.sh --build-only

# 只启动
./scripts/deploy.sh --start-only

# 只启动监控系统
./scripts/deploy.sh --monitoring

# 查看状态
./scripts/deploy.sh --status

# 清理所有
./scripts/deploy.sh --clean
```

---

## 手动部署

### 步骤 1: 构建应用

```bash
# 使用 sudo 构建
sudo docker-compose -f docker-compose.prod.yml build --no-cache
```

### 步骤 2: 启动应用

```bash
# 启动所有服务
sudo docker-compose -f docker-compose.prod.yml up -d

# 查看状态
sudo docker-compose -f docker-compose.prod.yml ps
```

### 步骤 3: 启动监控

```bash
# 启动监控服务
sudo docker-compose -f docker-compose.monitoring.yml up -d

# 查看监控状态
sudo docker-compose -f docker-compose.monitoring.yml ps
```

---

## 访问服务

### 应用服务

| 服务 | 地址 | 说明 |
|------|------|------|
| 前端 | http://localhost | React 前端 |
| API | http://localhost:8000 | REST API |
| API 文档 | http://localhost:8000/docs | Swagger UI |
| N8N | http://localhost:5678 | 工作流引擎 |

### 监控服务

| 服务 | 地址 | 说明 |
|------|------|------|
| Grafana | http://localhost:3000 | 监控仪表板 |
| Prometheus | http://localhost:9090 | 指标查询 |
| Alertmanager | http://localhost:9093 | 告警管理 |

---

## 常用命令

### 查看日志

```bash
# 查看所有服务日志
sudo docker-compose -f docker-compose.prod.yml logs -f

# 查看特定服务
sudo docker-compose -f docker-compose.prod.yml logs -f agentforge-api

# 查看监控日志
sudo docker-compose -f docker-compose.monitoring.yml logs -f prometheus
```

### 重启服务

```bash
# 重启所有
sudo docker-compose -f docker-compose.prod.yml restart

# 重启单个服务
sudo docker-compose -f docker-compose.prod.yml restart agentforge-api
```

### 停止服务

```bash
# 停止所有
sudo docker-compose -f docker-compose.prod.yml down

# 停止并删除数据卷
sudo docker-compose -f docker-compose.prod.yml down -v
```

---

## 故障排除

### 问题 1: Docker 权限错误

```bash
# 添加用户到 docker 组
sudo usermod -aG docker $USER
newgrp docker

# 或者使用 sudo
sudo docker-compose ...
```

### 问题 2: 构建失败

```bash
# 清理缓存
sudo docker builder prune -a -f

# 重新构建
sudo docker-compose -f docker-compose.prod.yml build --no-cache
```

### 问题 3: 端口冲突

```bash
# 查看端口占用
sudo lsof -i :8000
sudo lsof -i :5432
sudo lsof -i :6379

# 停止占用端口的服务或使用不同端口
```

---

## 验证部署

```bash
# 测试 API
curl http://localhost:8000/api/health

# 测试前端
curl http://localhost

# 测试 Prometheus
curl http://localhost:9090/-/healthy

# 测试 Grafana
curl http://localhost:3000/api/health
```

---

**最后更新**: 2026-03-30  
**版本**: v1.0.1
