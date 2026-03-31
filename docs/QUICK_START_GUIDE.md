# AgentForge 快速开始指南

## 📋 目录
1. [系统访问](#1-系统访问)
2. [登录系统](#2-登录系统)
3. [核心功能介绍](#3-核心功能介绍)
4. [API 文档](#4-api-文档)
5. [工作流引擎](#5-工作流引擎)
6. [常见问题](#6-常见问题)

---

## 1️⃣ 系统访问

### 服务地址

| 服务 | 本地访问地址 | 说明 |
|------|--------------|------|
| **前端界面** | http://localhost | 主用户界面 |
| **API 服务** | http://localhost:8000 | 后端 API |
| **API 文档** | http://localhost:8000/docs | Swagger UI 交互式文档 |
| **N8N 工作流** | http://localhost:5678 | 工作流引擎管理界面 |

---

## 2️⃣ 登录系统

### 默认账号

| 字段 | 值 |
|------|-----|
| 用户名 | `admin` |
| 密码 | `Admin@123` |
| 邮箱 | `admin@agentforge.local` |

### 登录步骤

1. 访问 http://localhost
2. 点击登录按钮
3. 输入用户名和密码
4. 点击登录

---

## 3️⃣ 核心功能介绍

### 3.1 AI 聊天助手

**功能描述**：与 AI 进行对话，获取帮助和建议。

**使用场景**：
- Fiverr 订单咨询
- 社交媒体文案生成
- 代码问题解答
- 日常问题咨询

### 3.2 Fiverr 订单管理

**功能描述**：自动化管理 Fiverr 订单流程。

**主要功能**：
- 订单自动报价
- 消息自动回复
- 订单状态跟踪
- 交付自动化

### 3.3 知识管理

**功能描述**：文档同步、知识库管理、检索增强。

**主要功能**：
- Obsidian 笔记同步
- Notion 数据库集成
- 向量搜索
- 知识图谱

### 3.4 社交媒体管理

**功能描述**：多平台内容发布和分析。

**支持平台**：
- LinkedIn
- Twitter/X
- Instagram
- Facebook
- Telegram

### 3.5 工作流自动化

**功能描述**：使用 N8N 可视化工作流引擎。

**预置工作流**：
- Fiverr 订单监控
- 知识同步
- 社交媒体发布
- 自动备份

---

## 4️⃣ API 文档

### 4.1 访问 Swagger UI

打开浏览器访问：http://localhost:8000/docs

### 4.2 健康检查

```bash
curl http://localhost:8000/api/health
```

响应示例：
```json
{
  "status": "healthy",
  "timestamp": "2026-03-31T00:00:00.000000",
  "version": "1.0.0",
  "services": {
    "llm": {
      "status": "healthy",
      "provider": "baidu_qianfan"
    },
    "memory": {
      "status": "healthy",
      "redis": true,
      "qdrant": true
    }
  }
}
```

### 4.3 主要 API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/health` | GET | 健康检查 |
| `/api/auth/login` | POST | 用户登录 |
| `/api/chat` | POST | 发送聊天消息 |
| `/api/orders` | GET/POST | 订单管理 |
| `/api/knowledge` | GET/POST | 知识管理 |
| `/api/backup` | POST | 数据备份 |

---

## 5️⃣ 工作流引擎 (N8N)

### 5.1 访问 N8N

打开浏览器访问：http://localhost:5678

### 5.2 默认账号

| 字段 | 值 |
|------|-----|
| 用户名 | `admin` |
| 密码 | 在 `.env` 文件中配置 |

### 5.3 预置工作流

N8N 中预置了以下工作流：

1. **Fiverr 订单监控** - 自动监控新订单
2. **知识库同步** - 同步 Obsidian/Notion 文档
3. **社交媒体发布** - 定时发布内容
4. **自动备份** - 定期数据备份

---

## 6️⃣ 常见问题

### Q1: 如何修改默认密码？

**A**: 登录系统后，进入设置页面修改密码，或直接修改数据库。

### Q2: 如何配置百度千帆 API？

**A**: 编辑 `.env` 文件，设置 `QIANFAN_API_KEY`。

### Q3: 如何备份数据？

**A**: 
1. 使用 API：`POST /api/backup`
2. 使用 N8N 工作流
3. 手动备份 Docker 数据卷

### Q4: 如何重启服务？

```bash
# 停止所有服务
sudo docker-compose -f docker-compose.prod.yml down

# 启动所有服务
sudo docker-compose -f docker-compose.prod.yml up -d

# 查看服务状态
sudo docker-compose -f docker-compose.prod.yml ps

# 查看日志
sudo docker-compose -f docker-compose.prod.yml logs -f
```

### Q5: 前端只显示空白页面？

**A**: 当前前端只部署了静态 index.html，完整的 React 前端需要单独构建。可以直接使用 API 进行开发。

---

## 📚 更多文档

- [用户手册](./USER_GUIDE.md) - 详细的功能说明
- [部署指南](./DEPLOYMENT.md) - 生产环境部署
- [API 文档](./api/README.md) - 完整的 API 参考

---

## 🆘 获取帮助

如果遇到问题：
1. 查看容器日志：`sudo docker-compose -f docker-compose.prod.yml logs`
2. 检查健康检查：`curl http://localhost:8000/api/health`
3. 参考项目文档：`docs/` 目录

---

**祝使用愉快！** 🎉
