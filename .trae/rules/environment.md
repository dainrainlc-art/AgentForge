# AgentForge 开发环境配置

## 1. 系统要求

### 1.1 操作系统

| 系统 | 版本要求 |
|------|----------|
| Windows | Windows 10/11 + WSL2 |
| Linux | Ubuntu 20.04+ / Debian 11+ |
| macOS | macOS 12+ |

### 1.2 硬件要求

| 资源 | 最低要求 | 推荐配置 |
|------|----------|----------|
| CPU | 4核心 | 8核心+ |
| 内存 | 8GB | 16GB+ |
| 存储 | 50GB SSD | 100GB+ SSD |
| 网络 | 稳定互联网连接 | - |

---

## 2. 软件环境要求

### 2.1 核心依赖

| 软件 | 版本要求 | 用途 |
|------|----------|------|
| Python | 3.12+ | 后端开发 |
| Node.js | 18+ | 前端开发 |
| Docker | 24+ | 容器化部署 |
| Docker Compose | 2.20+ | 服务编排 |
| Git | 2.40+ | 版本控制 |

### 2.2 可选工具

| 软件 | 用途 |
|------|------|
| VS Code | 代码编辑器 |
| DBeaver | 数据库管理 |
| Postman | API测试 |
| Redis Insight | Redis可视化 |

---

## 3. Python环境配置

### 3.1 安装Python 3.12+

#### Ubuntu/Debian

```bash
sudo apt update
sudo apt install python3.12 python3.12-venv python3-pip
```

#### macOS (使用Homebrew)

```bash
brew install python@3.12
```

#### Windows (WSL2)

```bash
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.12 python3.12-venv python3-pip
```

### 3.2 创建虚拟环境

```bash
cd /path/to/AgentForge
python3.12 -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
.\venv\Scripts\activate   # Windows
```

### 3.3 安装依赖

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 3.4 验证安装

```bash
python --version
pip list
```

---

## 4. Node.js环境配置

### 4.1 安装Node.js 18+

#### Ubuntu/Debian

```bash
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
```

#### macOS (使用Homebrew)

```bash
brew install node@18
```

#### Windows (WSL2)

```bash
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
```

### 4.2 安装前端依赖

```bash
cd frontend
npm install
```

### 4.3 验证安装

```bash
node --version
npm --version
```

---

## 5. Docker环境配置

### 5.1 安装Docker

#### Ubuntu/Debian

```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

#### macOS

```bash
brew install --cask docker
```

#### Windows

安装Docker Desktop并启用WSL2后端。

### 5.2 安装Docker Compose

```bash
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 5.3 验证安装

```bash
docker --version
docker-compose --version
```

### 5.4 Docker镜像加速 (可选)

```bash
# 配置阿里云镜像加速
./configure-aliyun-mirror.sh
```

---

## 6. 依赖管理

### 6.1 Python依赖 (requirements.txt)

```
# 核心框架
openai>=1.0.0
anthropic>=0.18.0
httpx>=0.25.0

# Web框架
fastapi>=0.109.0
uvicorn>=0.27.0
pydantic>=2.5.0

# 数据库
sqlalchemy>=2.0.0
asyncpg>=0.29.0
redis>=5.0.0

# 向量数据库
qdrant-client>=1.7.0

# 数据处理
pydantic-settings>=2.1.0
python-dotenv>=1.0.0
pyyaml>=6.0

# 工具库
python-multipart>=0.0.6
aiofiles>=23.2.0
tenacity>=8.2.0

# 日志
loguru>=0.7.0

# 测试
pytest>=7.4.0
pytest-asyncio>=0.23.0
pytest-cov>=4.1.0

# 代码质量
black>=24.1.0
ruff>=0.1.0
mypy>=1.8.0
```

### 6.2 Node.js依赖 (package.json)

```json
{
  "dependencies": {
    "axios": "^1.6.8",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.22.0"
  },
  "devDependencies": {
    "@tailwindcss/postcss": "^4.2.2",
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "@vitejs/plugin-react": "^4.2.0",
    "autoprefixer": "^10.4.27",
    "postcss": "^8.5.8",
    "tailwindcss": "^4.2.2",
    "typescript": "^5.4.2",
    "vite": "^5.2.0"
  }
}
```

### 6.3 更新依赖

```bash
# Python
pip install --upgrade pip
pip install -r requirements.txt --upgrade

# Node.js
npm update
```

---

## 7. 环境变量配置

### 7.1 创建环境变量文件

```bash
cp .env.example .env
```

### 7.2 环境变量说明 (.env.example)

```bash
# ===========================================
# 百度千帆配置 (必需)
# ===========================================
QIANFAN_API_KEY=your_qianfan_api_key_here

# ===========================================
# 数据库配置
# ===========================================
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=agentforge
POSTGRES_USER=agentforge
POSTGRES_PASSWORD=your_secure_postgres_password

# ===========================================
# Redis配置
# ===========================================
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# ===========================================
# n8n配置
# ===========================================
N8N_PORT=5678
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=your_n8n_password
N8N_WEBHOOK_URL=http://localhost:5678/webhook/

# ===========================================
# GitHub配置
# ===========================================
GITHUB_TOKEN=your_github_personal_access_token
GITHUB_REPO_OWNER=your_username
GITHUB_REPO_NAME=agentforge

# ===========================================
# Notion配置 (可选)
# ===========================================
NOTION_API_KEY=your_notion_integration_token
NOTION_DATABASE_ID=your_database_id

# ===========================================
# 社交媒体API配置 (可选)
# ===========================================
YOUTUBE_API_KEY=your_youtube_api_key
TWITTER_API_KEY=your_twitter_api_key
TWITTER_API_SECRET=your_twitter_api_secret
TWITTER_ACCESS_TOKEN=your_twitter_access_token
TWITTER_ACCESS_SECRET=your_twitter_access_secret
FACEBOOK_APP_ID=your_facebook_app_id
FACEBOOK_APP_SECRET=your_facebook_app_secret
FACEBOOK_PAGE_ACCESS_TOKEN=your_page_access_token
INSTAGRAM_ACCESS_TOKEN=your_instagram_access_token
LINKEDIN_CLIENT_ID=your_linkedin_client_id
LINKEDIN_CLIENT_SECRET=your_linkedin_client_secret

# ===========================================
# Fiverr配置 (可选)
# ===========================================
FIVERR_API_KEY=your_fiverr_api_key

# ===========================================
# Obsidian配置
# ===========================================
OBSIDIAN_VAULT_PATH=/path/to/your/obsidian/vault

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
# 外部访问配置 (可选)
# ===========================================
# PUBLIC_DOMAIN=your-domain.com
# WEBHOOK_URL=https://your-domain.com/webhook/
```

### 7.3 必需配置项

| 配置项 | 说明 | 获取方式 |
|--------|------|----------|
| QIANFAN_API_KEY | 百度千帆API密钥 | [百度千帆控制台](https://console.bce.baidu.com/qianfan/) |
| POSTGRES_PASSWORD | PostgreSQL密码 | 自定义设置 |
| SECRET_KEY | 应用密钥 | 使用`openssl rand -hex 32`生成 |

### 7.4 生成密钥

```bash
# 生成SECRET_KEY
openssl rand -hex 32

# 生成ENCRYPTION_KEY (AES-256)
openssl rand -base64 32
```

---

## 8. 本地开发启动流程

### 8.1 完整启动流程

```bash
# 1. 克隆项目
git clone https://github.com/your-username/AgentForge.git
cd AgentForge

# 2. 配置环境变量
cp .env.example .env
# 编辑.env文件，填写必要配置

# 3. 启动Docker服务
docker-compose up -d

# 4. 等待服务启动
sleep 10

# 5. 初始化数据库
docker-compose exec postgres psql -U agentforge -d agentforge -f /docker-entrypoint-initdb.d/01_schema.sql

# 6. 配置Python环境
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 7. 启动后端服务
uvicorn agentforge.api.main:app --reload --host 0.0.0.0 --port 8000

# 8. 配置前端环境 (新终端)
cd frontend
npm install
npm run dev
```

### 8.2 快速启动脚本

```bash
# 使用项目提供的启动脚本
./start-services.sh

# 或使用run.sh
./run.sh
```

### 8.3 服务访问地址

| 服务 | 地址 | 说明 |
|------|------|------|
| 前端 | http://localhost:5173 | Vite开发服务器 |
| 后端API | http://localhost:8000 | FastAPI服务 |
| API文档 | http://localhost:8000/docs | Swagger UI |
| N8N | http://localhost:5678 | 工作流引擎 |
| Qdrant | http://localhost:6333 | 向量数据库 |

---

## 9. Docker服务管理

### 9.1 服务列表

| 服务 | 容器名 | 端口 |
|------|--------|------|
| PostgreSQL | agentforge-postgres | 5432 |
| Redis | agentforge-redis | 6379 |
| Qdrant | agentforge-qdrant | 6333 |
| N8N | agentforge-n8n | 5678 |

### 9.2 常用命令

```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看服务日志
docker-compose logs -f
docker-compose logs -f postgres

# 停止所有服务
docker-compose down

# 停止并删除数据卷
docker-compose down -v

# 重启单个服务
docker-compose restart postgres

# 进入容器
docker-compose exec postgres bash

# 查看资源使用
docker stats
```

### 9.3 数据持久化

Docker数据卷位置：

```
postgres_data -> PostgreSQL数据
redis_data    -> Redis数据
qdrant_data   -> Qdrant数据
n8n_data      -> N8N工作流数据
```

---

## 10. 数据库初始化

### 10.1 PostgreSQL初始化

初始化脚本位于 `docker/init-db/01_schema.sql`。

```bash
# 手动执行初始化
docker-compose exec postgres psql -U agentforge -d agentforge -f /docker-entrypoint-initdb.d/01_schema.sql
```

### 10.2 连接数据库

```bash
# 使用psql
docker-compose exec postgres psql -U agentforge -d agentforge

# 或使用本地psql
psql -h localhost -p 5432 -U agentforge -d agentforge
```

### 10.3 数据库备份

```bash
# 备份
docker-compose exec postgres pg_dump -U agentforge agentforge > backup.sql

# 恢复
cat backup.sql | docker-compose exec -T postgres psql -U agentforge agentforge
```

---

## 11. 开发工具配置

### 11.1 VS Code推荐扩展

```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "dbaeumer.vscode-eslint",
    "esbenp.prettier-vscode",
    "ms-azuretools.vscode-docker",
    "bradlc.vscode-tailwindcss",
    "usernamehw.errorlens",
    "streetsidesoftware.code-spell-checker"
  ]
}
```

### 11.2 VS Code配置

```json
{
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "ms-python.black-formatter",
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter",
    "editor.codeActionsOnSave": {
      "source.organizeImports": "explicit"
    }
  },
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[typescriptreact]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.testing.pytestEnabled": true
}
```

### 11.3 PyCharm配置

1. 设置Python解释器为项目虚拟环境
2. 启用Black格式化器
3. 启用Ruff代码检查
4. 配置pytest作为测试运行器

---

## 12. 故障排除

### 12.1 常见问题

#### Docker服务无法启动

```bash
# 检查Docker状态
sudo systemctl status docker

# 检查端口占用
sudo lsof -i :5432
sudo lsof -i :6379
sudo lsof -i :6333
sudo lsof -i :5678

# 清理Docker资源
docker system prune -a
```

#### Python依赖安装失败

```bash
# 更新pip
pip install --upgrade pip setuptools wheel

# 清理缓存
pip cache purge

# 使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

#### 数据库连接失败

```bash
# 检查服务状态
docker-compose ps postgres

# 检查日志
docker-compose logs postgres

# 重启服务
docker-compose restart postgres
```

### 12.2 日志查看

```bash
# 查看后端日志
tail -f logs/app.log

# 查看Docker日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f postgres
docker-compose logs -f n8n
```

### 12.3 重置开发环境

```bash
# 停止所有服务
docker-compose down -v

# 删除虚拟环境
rm -rf venv

# 删除node_modules
rm -rf frontend/node_modules

# 重新开始
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd frontend && npm install
docker-compose up -d
```

---

## 13. 生产环境部署

### 13.1 使用生产配置

```bash
# 使用生产docker-compose配置
docker-compose -f docker-compose.base.yml -f docker-compose.prod.yml up -d
```

### 13.2 生产环境检查清单

- [ ] 更改所有默认密码
- [ ] 配置HTTPS
- [ ] 设置防火墙规则
- [ ] 配置日志轮转
- [ ] 设置数据库备份
- [ ] 配置监控告警
- [ ] 审查安全配置
