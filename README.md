# AgentForge

<p align="center">
  <img src="https://img.shields.io/badge/version-1.0.0-blue.svg" alt="Version">
  <img src="https://img.shields.io/badge/python-3.12%2B-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/node-18%2B-green.svg" alt="Node.js">
  <img src="https://img.shields.io/badge/license-MIT-yellow.svg" alt="License">
</p>

<p align="center">
  <b>AI驱动的Fiverr运营自动化助理系统</b><br>
  <i>智能、高效、可扩展的自动化运营解决方案</i>
</p>

---

## 🌟 项目简介

AgentForge 是一个基于 AI 的 Fiverr 运营自动化平台，旨在帮助自由职业者和企业自动化管理 Fiverr 订单、客户沟通、社交媒体营销等运营任务。系统采用先进的六层架构设计，支持自进化、多 Agent 协同工作，提供完整的自动化解决方案。

## 🚀 核心特性

### 1. AI 智能助手
- 🤖 **多模型支持**: GLM-5, Kimi-K2.5, DeepSeek, MiniMax
- 🧠 **自进化系统**: 自动优化提示词和工作流
- 💬 **智能对话**: 自然语言处理，上下文理解
- 📝 **内容生成**: 自动文案、邮件、回复生成

### 2. Fiverr 自动化
- 📦 **订单管理**: 自动监控、报价、交付
- 💬 **客户沟通**: 智能回复、消息模板
- 📊 **数据分析**: 订单统计、收入分析
- 🎯 **优化建议**: 自动优化 Gig 和 Profile

### 3. 社交媒体营销
- 📱 **多平台支持**: LinkedIn, Twitter, Instagram, Facebook
- 📝 **内容发布**: 自动排版、定时发布
- 📈 **数据分析**: 粉丝增长、互动分析
- 🔄 **内容同步**: 一键多平台同步

### 4. 知识管理
- 📚 **Obsidian 同步**: 双向同步笔记
- 🗂️ **Notion 集成**: 数据库自动同步
- 🔍 **向量搜索**: 语义检索、知识图谱
- 📄 **文档处理**: 自动分类、标签管理

### 5. 工作流引擎
- ⚡ **N8N 集成**: 可视化工作流设计
- 🔧 **技能系统**: 模块化技能管理
- 🔌 **插件扩展**: 丰富的插件生态
- 🔄 **自动化**: 定时任务、事件触发

## 🏗️ 技术架构

```
┌─────────────────────────────────────────────────────────────┐
│                     用户交互层 (UI Layer)                    │
│         React + TypeScript + Tailwind CSS + Vite            │
├─────────────────────────────────────────────────────────────┤
│                     集成接口层 (API Layer)                   │
│              FastAPI + WebSocket + RESTful API              │
├─────────────────────────────────────────────────────────────┤
│                     业务逻辑层 (Business Layer)              │
│         Fiverr管理 | 社交媒体 | 知识管理 | 工作流           │
├─────────────────────────────────────────────────────────────┤
│                     AI 能力层 (AI Layer)                     │
│     GLM-5 | Kimi-K2.5 | DeepSeek | MiniMax | 自进化        │
├─────────────────────────────────────────────────────────────┤
│                     数据存储层 (Data Layer)                  │
│       PostgreSQL | Redis | Qdrant (向量数据库)              │
├─────────────────────────────────────────────────────────────┤
│                     基础设施层 (Infra Layer)                 │
│     Docker | Docker Compose | Nginx | 监控系统              │
└─────────────────────────────────────────────────────────────┘
```

## 📦 快速开始

### 环境要求
- Python 3.12+
- Node.js 18+
- Docker & Docker Compose

### 安装步骤

```bash
# 1. 克隆项目
git clone https://github.com/dainrainlc/agentforge.git
cd agentforge

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，配置 API 密钥

# 3. 启动服务
./start-services.sh

# 4. 访问系统
# 前端: http://localhost
# API: http://localhost:8000
# API文档: http://localhost:8000/docs
```

### Docker 部署

```bash
# 启动所有服务
docker-compose -f docker-compose.prod.yml up -d

# 查看状态
docker-compose -f docker-compose.prod.yml ps

# 查看日志
docker-compose -f docker-compose.prod.yml logs -f
```

## 📚 文档

- [快速开始指南](docs/QUICK_START_GUIDE.md)
- [部署指南](docs/DEPLOYMENT.md)
- [API 文档](docs/api/README.md)
- [架构设计](docs/architecture/overview.md)
- [用户手册](docs/USER_GUIDE.md)

## 🧪 测试

```bash
# 运行单元测试
pytest tests/unit/ -v

# 运行集成测试
pytest tests/integration/ -v

# 运行性能测试
python tests/performance/benchmark.py

# 运行安全扫描
bandit -r agentforge/ -f json
safety check -r requirements.txt
```

## 🔒 安全性

- ✅ Bandit 代码安全扫描
- ✅ Safety 依赖漏洞扫描
- ✅ JWT 认证授权
- ✅ 速率限制保护
- ✅ 输入验证和清理
- ✅ HTTPS 支持

## 🚀 CI/CD

项目集成了完整的 CI/CD 管道：

- 🔍 代码质量检查 (Ruff, Black, MyPy)
- 🧪 自动化测试 (单元测试、集成测试)
- 🛡️ 安全扫描 (Bandit, Safety, Trivy)
- 🐳 Docker 镜像构建
- 📚 文档自动生成
- 🚀 自动发布

## 🛠️ 技术栈

### 后端
- **框架**: FastAPI
- **数据库**: PostgreSQL, Redis, Qdrant
- **AI**: OpenAI, Anthropic, 百度千帆
- **任务队列**: Celery
- **测试**: pytest

### 前端
- **框架**: React 18
- **语言**: TypeScript
- **样式**: Tailwind CSS
- **构建**: Vite
- **状态**: React Hooks

### 运维
- **容器**: Docker, Docker Compose
- **监控**: Prometheus, Grafana, Loki
- **网关**: Nginx
- **工作流**: N8N

## 📈 性能指标

- API 响应时间: < 200ms
- 数据库查询: < 100ms
- 缓存命中率: > 90%
- 并发支持: 1000+ 用户

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📄 许可证

本项目基于 [MIT](LICENSE) 许可证开源。

## 🙏 致谢

- [FastAPI](https://fastapi.tiangolo.com/) - 高性能 Web 框架
- [React](https://react.dev/) - 前端框架
- [N8N](https://n8n.io/) - 工作流自动化
- [百度千帆](https://cloud.baidu.com/) - AI 模型服务

---

<p align="center">
  <b>Made with ❤️ by AgentForge Team</b><br>
  <a href="https://github.com/dainrainlc/agentforge">GitHub</a> •
  <a href="docs/">Documentation</a> •
  <a href="https://github.com/dainrainlc/agentforge/issues">Issues</a>
</p>
