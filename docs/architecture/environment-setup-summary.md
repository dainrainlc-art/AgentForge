# AgentForge 环境搭建总结

## 📋 完成情况

### ✅ 已完成的工作

| 任务 | 状态 | 说明 |
|------|------|------|
| 检查Docker环境 | ✅ 完成 | Docker 28.2.2 已安装 |
| 创建.env配置文件 | ✅ 完成 | 已生成安全密码和配置 |
| **配置百度千帆API Key** | ✅ 完成 | 用户已配置API Key |
| 准备Docker Compose配置 | ✅ 完成 | docker-compose.base.yml已创建 |
| 创建目录结构 | ✅ 完成 | data/n8n、workflows、vault目录已创建 |
| **创建启动脚本** | ✅ 完成 | start/stop/logs脚本已创建 |
| **配置Docker代理** | ✅ 完成 | 使用 192.168.31.230:7897 |
| **拉取Docker镜像** | ✅ 完成 | n8n、postgres、redis、qdrant |
| **启动基础服务** | ✅ 完成 | 所有服务已启动并运行 |
| **验证服务健康状态** | ✅ 完成 | 所有服务健康运行 |

## 📁 已创建的文件

```
AgentForge/
├── .env                                    # 环境配置文件（已配置API Key！）
├── docker-compose.base.yml                 # 基础服务Docker Compose配置
├── start-services.sh                       # 服务启动脚本
├── stop-services.sh                        # 服务停止脚本
├── logs-services.sh                        # 日志查看脚本
├── configure-docker-proxy.sh              # Docker代理配置脚本
├── configure-docker-mirror.sh             # Docker镜像加速器配置脚本
├── configure-aliyun-mirror.sh             # 阿里云镜像源配置脚本
├── docker/
│   ├── docker-compose.yml                  # 完整Docker Compose配置
│   └── init-db/
│       └── 01_schema.sql                   # 数据库初始化脚本
├── data/
│   └── n8n/                                # N8N数据目录
├── workflows/                               # N8N工作流目录
└── vault/                                   # Obsidian知识库目录
```

## 🔐 生成的安全凭证

以下凭证已在.env文件中自动生成：

| 配置项 | 值 | 说明 |
|--------|-----|------|
| **QIANFAN_API_KEY** | **已配置** ✅ | 百度千帆API Key |
| POSTGRES_PASSWORD | 6HBUboJc1-YlBqNmNZynCw | 数据库密码 |
| N8N_PASSWORD | Rg2pX5rPciFyCU73 | N8N登录密码 |
| SECRET_KEY | 4dUp8KI9EMfobBJ2nxRX6OoIXdYpEb-if8xBRWjQf1k | 应用密钥 |
| ENCRYPTION_KEY | 547f281f39e0288244572d84bc25831a44209a8b7c306e9592c8b58f5db4c5f9 | 加密密钥 |

**重要提示**：请妥善保管这些凭证！

## 🚀 服务状态

✅ **所有基础服务已成功启动并运行！**

### 当前运行的服务

| 服务 | 状态 | 访问地址 |
|------|------|----------|
| N8N | ✅ 运行中 | http://localhost:5678 |
| PostgreSQL | ✅ 健康运行 | localhost:5432 |
| Redis | ✅ 运行中 | localhost:6379 |
| Qdrant | ✅ 运行中 | http://localhost:6333 |

## 🌐 服务访问

| 服务 | 访问地址 | 默认凭据 |
|------|----------|----------|
| N8N | http://localhost:5678 | admin / Rg2pX5rPciFyCU73 |
| PostgreSQL | localhost:5432 | agentforge / 6HBUboJc1-YlBqNmNZynCw |
| Redis | localhost:6379 | 无密码 |
| Qdrant | http://localhost:6333 | 无密码 |

## 📝 服务说明

### 基础服务（已配置）

| 服务 | 镜像 | 端口 | 用途 |
|------|------|------|------|
| n8n | n8nio/n8n:latest | 5678 | 工作流引擎 |
| postgres | postgres:15-alpine | 5432 | 主数据库 |
| redis | redis:7-alpine | 6379 | 缓存与会话 |
| qdrant | qdrant/qdrant:latest | 6333/6334 | 向量数据库 |

### AgentForge Core（待开发）

AgentForge Core服务需要先开发Dockerfile，然后才能添加到docker-compose.yml中。

## 🔧 快速开始

### 1. 查看服务状态

```bash
# 查看当前服务状态
sudo docker-compose -f docker-compose.base.yml ps
```

### 2. 查看服务日志

```bash
# 查看所有服务日志
./logs-services.sh

# 查看特定服务日志（例如 n8n）
./logs-services.sh n8n

# 查看特定服务日志（例如 postgres）
./logs-services.sh postgres
```

### 3. 停止服务

```bash
# 停止所有服务
./stop-services.sh
```

### 4. 重启服务

```bash
# 如果需要重启服务
./stop-services.sh
./start-services.sh
```

## 🔧 故障排查

### Docker代理配置

当前Docker已配置使用代理：`http://192.168.31.230:7897`

如需重新配置代理：
```bash
./configure-docker-proxy.sh <代理地址>
# 示例：./configure-docker-proxy.sh http://192.168.31.230:7897
```

### Docker权限问题

已通过创建使用sudo的启动脚本来解决此问题，直接使用脚本即可。

### 端口被占用

如果端口被占用，可以修改`.env`文件中的端口配置：
```bash
N8N_PORT=5679
POSTGRES_PORT=5433
REDIS_PORT=6380
```

### 服务无法启动

查看服务日志排查问题：
```bash
# 使用日志脚本查看
./logs-services.sh

# 或者直接使用
sudo docker-compose -f docker-compose.base.yml logs -f
```

## 📚 相关文档

- [系统架构总览](./system-overview.md)
- [部署架构设计](./deployment-architecture.md)
- [安全架构设计](./security-architecture.md)

---

**🎉 环境搭建完成！所有基础服务已成功启动并运行！**
