# AgentForge

Fiverr运营自动化智能助理系统 - 基于GLM-5和N8N的AI驱动自动化平台。

## 六层架构设计

AgentForge 采用六层架构设计，实现清晰的关注点分离和高度可扩展性：

### 架构层次

| 层级 | 目录 | 职责 |
|------|------|------|
| 基础设施层 | `infrastructure/` | Docker、K8s、部署脚本 |
| 数据存储层 | `data/` | 数据库迁移、初始数据、备份 |
| AI能力层 | `agentforge/` | 核心AI模块、技能、记忆、LLM集成 |
| 业务逻辑层 | `workflows/` | 业务引擎、n8n工作流 |
| 集成接口层 | `integrations/` | REST API、外部服务、Webhooks |
| 用户交互层 | `frontend/` | React前端、CLI工具 |

## 目录结构

```
AgentForge/
├── infrastructure/          # 基础设施层
│   ├── docker/             # Docker配置
│   ├── scripts/            # 部署脚本
│   └── k8s/                # Kubernetes配置
├── data/                   # 数据存储层
│   ├── migrations/         # 数据库迁移
│   ├── seeds/              # 初始数据
│   └── backups/            # 数据备份
├── agentforge/             # AI能力层（核心）
│   ├── core/               # 核心模块（自进化、记忆系统）
│   ├── skills/             # Agent技能模块
│   ├── memory/             # 长期记忆存储
│   ├── llm/                # LLM集成（百度千帆）
│   └── prompts/            # Prompt模板
├── workflows/              # 业务逻辑层
│   ├── engines/            # 业务引擎
│   │   ├── fiverr/        # Fiverr运营引擎
│   │   ├── social/        # 社交媒体引擎
│   │   ├── knowledge/     # 知识管理引擎
│   │   └── communication/ # 客户沟通引擎
│   └── n8n/                # n8n工作流配置
├── integrations/           # 集成接口层
│   ├── api/                # REST API
│   ├── external/           # 外部服务集成
│   │   ├── fiverr/        # Fiverr API
│   │   ├── notion/        # Notion API
│   │   ├── obsidian/      # Obsidian集成
│   │   └── social/        # 社交媒体API
│   └── webhooks/           # Webhook处理
├── frontend/               # 用户交互层
│   ├── src/
│   │   ├── components/    # UI组件
│   │   ├── pages/         # 页面
│   │   ├── hooks/         # React Hooks
│   │   └── utils/         # 工具函数
│   └── public/
├── cli/                    # 命令行工具
├── tests/                  # 测试
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── .backup/                # 备份目录
├── .trae/                  # Trae配置
├── docs/                   # 项目文档
├── docker/                 # Docker配置（遗留）
├── n8n-workflows/          # n8n工作流定义
├── .env                    # 环境配置
├── requirements.txt        # Python依赖
└── README.md
```

## 各层职责说明

### 1. 基础设施层 (infrastructure/)
- Docker容器配置
- Kubernetes部署配置
- CI/CD脚本
- 环境初始化脚本

### 2. 数据存储层 (data/)
- 数据库迁移脚本
- 初始数据种子
- 数据备份与恢复
- 数据模型定义

### 3. AI能力层 (agentforge/)
- **core/**: 自进化引擎、记忆系统核心
- **skills/**: 可插拔的Agent技能模块
- **memory/**: 长期记忆存储与管理
- **llm/**: 百度千帆GLM-5集成
- **prompts/**: Prompt模板管理

### 4. 业务逻辑层 (workflows/)
- **engines/**: 各业务领域引擎
  - Fiverr运营自动化
  - 社交媒体管理
  - 知识库管理
  - 客户沟通自动化
- **n8n/**: n8n工作流配置

### 5. 集成接口层 (integrations/)
- **api/**: REST API端点
- **external/**: 外部服务集成适配器
- **webhooks/**: Webhook接收与处理

### 6. 用户交互层 (frontend/)
- React前端应用
- CLI命令行工具
- 用户界面组件

## 快速开始

### 前置要求

- Python 3.12+
- Docker 和 Docker Compose
- 百度千帆API Key

### 1. 环境配置

确保已配置好 `.env` 文件中的百度千帆API Key：
```env
QIANFAN_API_KEY=your_api_key_here
```

### 2. 启动基础服务（Docker）

```bash
./start-services.sh
```

### 3. 创建虚拟环境并安装依赖

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. 启动AgentForge API

```bash
./run.sh
```

## 服务访问

| 服务 | 地址 |
|------|------|
| AgentForge API | http://localhost:8000 |
| API 文档 (Swagger) | http://localhost:8000/docs |
| N8N 工作流 | http://localhost:5678 |
| PostgreSQL | localhost:5432 |
| Redis | localhost:6379 |
| Qdrant | http://localhost:6333 |

## 核心功能

### 1. 意图识别
自动识别用户意图，包括：
- Fiverr订单管理
- 内容创作
- 社交媒体营销
- 知识管理
- 客户沟通

### 2. GLM-5集成
- 基于百度千帆GLM-5核心模型
- 支持多语言处理
- 智能内容创作
- 专业客户沟通

### 3. 多数据库支持
- **PostgreSQL**: 结构化业务数据
- **Redis**: 缓存与会话管理
- **Qdrant**: 向量数据库与语义搜索

### 4. N8N工作流
- 自动化工作流编排
- 事件驱动架构
- 定时任务调度

## 开发指南

### 代码质量检查
```bash
black agentforge/
ruff agentforge/
mypy agentforge/
```

### 运行测试
```bash
pytest tests/
```

## 配置说明

### 环境变量 (.env)

| 变量 | 说明 | 必填 |
|------|------|------|
| QIANFAN_API_KEY | 百度千帆API Key | ✅ |
| POSTGRES_PASSWORD | PostgreSQL密码 | ✅ |
| N8N_BASIC_AUTH_PASSWORD | N8N密码 | ✅ |
| SECRET_KEY | 应用密钥 | ✅ |
| ENCRYPTION_KEY | 加密密钥 | ✅ |

## 安全说明

- 所有敏感数据存储在本地
- API密钥加密存储
- 最小权限原则
- 完整的操作审计日志

## 许可证

MIT License
