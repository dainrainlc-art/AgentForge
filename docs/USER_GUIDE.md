# AgentForge 用户手册

> 完整的用户使用指南，帮助您快速上手并充分利用 AgentForge 系统

---

## 📖 目录

1. [快速开始](#快速开始)
2. [功能使用说明](#功能使用说明)
3. [常见问题解答](#常见问题解答)

---

## 🚀 快速开始

### 系统要求

在开始之前，请确保您的系统满足以下要求：

**硬件要求**：
- CPU: 4 核心以上
- 内存：8GB 以上（推荐 16GB）
- 存储：50GB 可用空间
- 网络：稳定的互联网连接

**软件要求**：
- 操作系统：Linux (Ubuntu 20.04+) / macOS 12+ / Windows 10+ (WSL2)
- Docker: 24+
- Docker Compose: 2.20+
- Python: 3.12+（仅开发需要）
- Node.js: 18+（仅前端开发需要）

### 环境配置步骤

#### 1. 克隆项目

```bash
git clone https://github.com/your-username/AgentForge.git
cd AgentForge
```

#### 2. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，配置必要的变量
# 至少需要配置以下内容：
# QIANFAN_API_KEY=your_api_key_here
# POSTGRES_PASSWORD=your_secure_password
# SECRET_KEY=your_secret_key
```

**必需的环境变量**：
- `QIANFAN_API_KEY` - 百度千帆 API 密钥
- `POSTGRES_PASSWORD` - PostgreSQL 数据库密码
- `SECRET_KEY` - 应用密钥（使用 `openssl rand -hex 32` 生成）

#### 3. 启动 Docker 服务

```bash
# 启动所有服务（PostgreSQL、Redis、Qdrant、N8N）
docker-compose up -d

# 查看服务状态
docker-compose ps

# 等待服务启动（约 30 秒）
sleep 30
```

#### 4. 初始化数据库

```bash
# 执行数据库初始化脚本
docker-compose exec postgres psql -U agentforge -d agentforge -f /docker-entrypoint-initdb.d/01_schema.sql
```

#### 5. 启动应用

```bash
# 配置 Python 环境
python3.12 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 启动后端服务
uvicorn agentforge.api.main:app --reload --host 0.0.0.0 --port 8000

# （新终端）启动前端服务
cd frontend
npm install
npm run dev
```

#### 6. 访问应用

- **前端界面**: http://localhost:5173
- **API 文档**: http://localhost:8000/docs
- **N8N 工作流**: http://localhost:5678

### 第一个技能示例

让我们创建一个简单的"问候技能"：

#### 步骤 1: 创建技能定义文件

创建文件 `agentforge/skills/greeting_skill.json`：

```json
{
  "name": "问候技能",
  "version": "1.0.0",
  "description": "发送问候消息",
  "trigger": {
    "type": "manual"
  },
  "actions": [
    {
      "type": "send_message",
      "params": {
        "to": "user",
        "subject": "问候",
        "content": "您好！这是一个自动发送的问候消息。"
      }
    }
  ],
  "enabled": true,
  "tags": ["greeting", "demo"],
  "author": "User"
}
```

#### 步骤 2: 通过 API 创建技能

```bash
curl -X POST http://localhost:8000/api/skills \
  -H "Content-Type: application/json" \
  -d '{
    "name": "问候技能",
    "version": "1.0.0",
    "description": "发送问候消息",
    "trigger": {"type": "manual"},
    "actions": [
      {
        "type": "send_message",
        "params": {
          "to": "user",
          "subject": "问候",
          "content": "您好！这是自动问候。"
        }
      }
    ],
    "enabled": true,
    "tags": ["greeting"]
  }'
```

#### 步骤 3: 执行技能

```bash
curl -X POST http://localhost:8000/api/skills/问候技能/trigger \
  -H "Content-Type: application/json" \
  -d '{}'
```

### 第一个工作流示例

创建一个简单的"订单处理工作流"：

#### 步骤 1: 创建工作流定义文件

创建文件 `agentforge/workflows/order_workflow.yaml`：

```yaml
name: 订单处理工作流
version: "1.0.0"
description: 自动处理新订单
trigger:
  type: manual
workflow:
  - name: 发送确认消息
    type: action
    action_type: send_message
    params:
      to: "{{customer_id}}"
      subject: "订单确认"
      content: "感谢您的订单！"
    timeout: 30
    retry: 3
    on_error: continue
  - name: 创建任务
    type: action
    action_type: create_task
    params:
      title: "处理订单 #{{order_id}}"
      description: "新订单需要处理"
      priority: high
    timeout: 30
    retry: 3
    on_error: abort
enabled: true
tags:
  - order
  - demo
```

#### 步骤 2: 通过 API 创建工作流

```bash
curl -X POST http://localhost:8000/api/workflows \
  -H "Content-Type: application/json" \
  -d '{
    "name": "订单处理工作流",
    "version": "1.0.0",
    "description": "自动处理新订单",
    "trigger": {"type": "manual"},
    "workflow": [
      {
        "name": "发送确认消息",
        "type": "action",
        "action_type": "send_message",
        "params": {
          "to": "customer",
          "subject": "订单确认",
          "content": "感谢订单！"
        }
      }
    ],
    "enabled": true
  }'
```

#### 步骤 3: 执行工作流

```bash
curl -X POST http://localhost:8000/api/workflows/订单处理工作流/execute \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "123",
    "order_id": "456"
  }'
```

---

## 💡 功能使用说明

### 技能系统使用指南

#### 什么是技能？

技能是预定义的动作序列，可以自动执行特定任务。每个技能包含：
- **触发器**: 定义技能何时被触发（手动、定时、事件）
- **动作**: 定义技能执行的具体操作
- **参数**: 动作执行时需要的数据

#### 技能类型

1. **手动触发技能**: 通过 API 或界面手动触发
2. **定时技能**: 按 Cron 表达式定时执行
3. **事件触发技能**: 监听特定事件自动触发

#### 创建技能

**方法 1: JSON 文件**

在 `agentforge/skills/` 目录创建 `.json` 文件：

```json
{
  "name": "技能名称",
  "version": "1.0.0",
  "description": "技能描述",
  "trigger": {
    "type": "manual",
    "cron": "0 9 * * *",
    "event_type": "event_name",
    "conditions": []
  },
  "actions": [
    {
      "type": "action_type",
      "params": {},
      "timeout": 30,
      "retry": 3,
      "on_error": "abort"
    }
  ],
  "enabled": true,
  "tags": ["tag1", "tag2"],
  "author": "作者"
}
```

**方法 2: API 创建**

```bash
POST /api/skills
Content-Type: application/json

{
  "name": "技能名称",
  ...
}
```

#### 动作类型

| 动作类型 | 说明 | 参数示例 |
|---------|------|---------|
| `send_message` | 发送消息 | `{"to": "user", "content": "消息内容"}` |
| `ai_generate` | AI 生成内容 | `{"model": "glm-5", "prompt": "生成内容"}` |
| `create_task` | 创建任务 | `{"title": "任务标题", "priority": "high"}` |
| `http_request` | HTTP 请求 | `{"method": "GET", "url": "http://..."}` |
| `query_data` | 数据查询 | `{"type": "orders", "params": {...}}` |

#### 变量替换

在参数中使用 `{{variable_name}}` 格式的变量：

```json
{
  "actions": [
    {
      "type": "send_message",
      "params": {
        "to": "{{customer_id}}",
        "content": "您好，{{customer_name}}！"
      }
    }
  ]
}
```

#### 管理技能

```bash
# 获取技能列表
GET /api/skills

# 获取技能详情
GET /api/skills/{skill_name}

# 启用技能
POST /api/skills/{skill_name}/enable

# 禁用技能
POST /api/skills/{skill_name}/disable

# 删除技能
DELETE /api/skills/{skill_name}

# 触发技能
POST /api/skills/{skill_name}/trigger
```

### 工作流系统使用指南

#### 什么是工作流？

工作流是复杂的动作序列，支持条件判断、并行执行等高级功能。使用 YAML 格式定义。

#### 工作流组件

1. **触发器**: 手动、定时、事件
2. **步骤**: 动作、条件、并行
3. **变量**: 在工作流中传递数据

#### 步骤类型

**动作步骤 (action)**:
```yaml
- name: 步骤名称
  type: action
  action_type: send_message
  params:
    to: "user"
  timeout: 30
  retry: 3
  on_error: continue
```

**条件步骤 (condition)**:
```yaml
- name: 条件判断
  type: condition
  conditions:
    - field: value
      operator: gt
      value: 10
```

**并行步骤 (parallel)**:
```yaml
- name: 并行执行
  type: parallel
  steps:
    - name: 子步骤 1
      type: action
      ...
    - name: 子步骤 2
      type: action
      ...
```

#### 条件操作符

| 操作符 | 说明 | 示例 |
|-------|------|------|
| `eq` | 等于 | `field: value, operator: eq, value: 10` |
| `ne` | 不等于 | `field: value, operator: ne, value: 10` |
| `gt` | 大于 | `field: value, operator: gt, value: 10` |
| `lt` | 小于 | `field: value, operator: lt, value: 10` |
| `gte` | 大于等于 | `field: value, operator: gte, value: 10` |
| `lte` | 小于等于 | `field: value, operator: lte, value: 10` |
| `contains` | 包含 | `field: text, operator: contains, value: "keyword"` |
| `exists` | 存在 | `field: value, operator: exists, value: true` |

#### 错误处理策略

- `abort`: 中止工作流（默认）
- `continue`: 继续执行下一步
- `retry`: 重试（使用 retry 次数）

#### 管理工作流

```bash
# 获取工作流列表
GET /api/workflows

# 获取工作流详情
GET /api/workflows/{name}

# 创建工作流
POST /api/workflows

# 更新工作流
PUT /api/workflows/{name}

# 删除工作流
DELETE /api/workflows/{name}

# 启用工作流
POST /api/workflows/{name}/enable

# 禁用工作流
POST /api/workflows/{name}/disable

# 执行工作流
POST /api/workflows/{name}/execute
```

### 插件系统使用指南

#### 什么是插件？

插件是可扩展系统功能的模块，提供额外的能力，如天气查询、汇率转换、翻译等。

#### 插件类型

1. **动作插件 (ActionPlugin)**: 执行特定动作
2. **触发器插件 (TriggerPlugin)**: 提供触发器能力
3. **数据插件 (DataPlugin)**: 提供数据源
4. **AI 插件 (AIPlugin)**: 提供 AI 能力

#### 预置插件

| 插件名称 | 功能 | 能力 |
|---------|------|------|
| `weather` | 天气查询 | `action`, `weather_query` |
| `currency` | 汇率转换 | `action`, `currency_conversion` |
| `translation` | 翻译 | `action`, `translation` |
| `file` | 文件处理 | `action`, `file_operation` |
| `calendar` | 日历和提醒 | `action`, `calendar`, `reminder` |

#### 使用插件

**通过 Python 代码**:

```python
from agentforge.core.plugin_manager import PluginManager

# 初始化管理器
plugin_manager = PluginManager()
await plugin_manager.initialize()

# 获取插件
calendar_plugin = plugin_manager.get_plugin("calendar")

# 执行插件
result = await calendar_plugin.execute({
    "operation": "get_date"
})
print(result)  # {'date': '2026-03-30', 'time': '12:00:00', ...}
```

**在技能中使用插件**:

```python
# 注册插件处理器
async def calendar_handler(params: dict, context):
    plugin = plugin_manager.get_plugin("calendar")
    return await plugin.execute(params)

skill_manager.register_action_handler("calendar_plugin", calendar_handler)
```

#### 管理插件

```python
# 列出所有插件
plugins = plugin_manager.list_plugins()

# 获取插件名称列表
names = plugin_manager.get_plugin_names()

# 启用插件
plugin_manager.enable_plugin("weather")

# 禁用插件
plugin_manager.disable_plugin("currency")

# 获取插件能力
capabilities = plugin_manager.get_plugin_capabilities("calendar")

# 按能力筛选插件
action_plugins = plugin_manager.get_plugins_by_capability("action")
```

#### 创建自定义插件

```python
from agentforge.core.plugin_base import ActionPlugin

class MyPlugin(ActionPlugin):
    name = "my_plugin"
    version = "1.0.0"
    description = "我的插件"
    
    async def initialize(self):
        """初始化插件"""
        self.enable()
    
    async def shutdown(self):
        """关闭插件"""
        self.disable()
    
    async def execute(self, params: dict, context=None) -> dict:
        """执行插件逻辑"""
        # 实现你的逻辑
        return {"result": "success"}
```

将插件文件放在 `agentforge/plugins/` 目录，系统会自动加载。

### API 使用指南

#### 认证

所有 API 端点都需要认证。在请求头中添加：

```
Authorization: Bearer YOUR_API_KEY
```

#### 基础 URL

- 开发环境：`http://localhost:8000/api`
- 生产环境：`https://your-domain.com/api`

#### 主要 API 端点

**技能 API**:
- `GET /skills` - 获取技能列表
- `POST /skills` - 创建技能
- `POST /skills/{name}/trigger` - 触发技能

**工作流 API**:
- `GET /workflows` - 获取工作流列表
- `POST /workflows` - 创建工作流
- `POST /workflows/{name}/execute` - 执行工作流

**事件 API**:
- `POST /events/trigger` - 触发事件

#### API 响应格式

成功响应：
```json
{
  "success": true,
  "data": {...},
  "message": "操作成功"
}
```

错误响应：
```json
{
  "success": false,
  "error": "错误代码",
  "message": "错误描述"
}
```

#### 使用 Swagger UI

访问 http://localhost:8000/docs 查看完整的 API 文档和测试端点。

---

## ❓ 常见问题解答

### 安装和配置问题

#### Q1: Docker 服务无法启动怎么办？

**A**: 检查以下几点：
1. 确认 Docker 已安装并运行：`sudo systemctl status docker`
2. 检查端口占用：`sudo lsof -i :5432`（PostgreSQL 端口）
3. 查看 Docker 日志：`docker-compose logs -f`
4. 清理 Docker 资源：`docker system prune -a`

#### Q2: 环境变量如何配置？

**A**: 
1. 复制模板：`cp .env.example .env`
2. 编辑 `.env` 文件
3. 至少配置：
   - `QIANFAN_API_KEY` - 从百度千帆控制台获取
   - `POSTGRES_PASSWORD` - 自定义安全密码
   - `SECRET_KEY` - 使用 `openssl rand -hex 32` 生成

#### Q3: 数据库连接失败怎么办？

**A**:
1. 检查 PostgreSQL 服务：`docker-compose ps postgres`
2. 查看日志：`docker-compose logs postgres`
3. 确认环境变量正确
4. 重启服务：`docker-compose restart postgres`

#### Q4: 依赖安装失败怎么办？

**A**:
```bash
# 更新 pip
pip install --upgrade pip setuptools wheel

# 清理缓存
pip cache purge

# 使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

#### Q5: 前端服务无法启动怎么办？

**A**:
1. 确认 Node.js 版本：`node --version`（需要 18+）
2. 删除 node_modules 重新安装：`rm -rf node_modules && npm install`
3. 检查端口占用：5173
4. 清除缓存：`npm run clean`

### 技能相关问题

#### Q6: 技能执行失败怎么办？

**A**:
1. 检查技能定义是否正确（JSON 格式）
2. 查看技能日志
3. 确认动作处理器已注册
4. 检查变量替换是否正确

#### Q7: 如何调试技能？

**A**:
1. 启用详细日志：设置 `LOG_LEVEL=DEBUG`
2. 使用 API 逐个触发动作
3. 检查执行上下文变量
4. 查看技能执行历史

#### Q8: 技能可以并发执行吗？

**A**: 可以。技能系统支持并发执行，但需要注意：
- 数据库连接池大小
- API 速率限制
- 资源竞争问题

### 工作流相关问题

#### Q9: 工作流执行超时怎么办？

**A**:
1. 增加步骤的 `timeout` 值
2. 优化慢动作
3. 使用异步动作
4. 添加重试机制

#### Q10: 如何实现工作流分支？

**A**: 使用条件步骤：
```yaml
- name: 条件判断
  type: condition
  conditions:
    - field: order_value
      operator: gt
      value: 100

- name: 大额订单处理
  type: action
  action_type: ...
```

#### Q11: 工作流如何传递数据？

**A**: 使用变量：
```yaml
workflow:
  - name: 步骤 1
    action_type: query_data
    # 结果自动存储到 {{data}}
  
  - name: 步骤 2
    action_type: send_message
    params:
      content: "{{data}}"  # 使用步骤 1 的结果
```

### 插件相关问题

#### Q12: 插件加载失败怎么办？

**A**:
1. 检查插件文件是否在 `agentforge/plugins/` 目录
2. 确认插件类继承自正确的基类
3. 检查插件依赖是否安装
4. 查看日志：`docker-compose logs -f`

#### Q13: 如何禁用某个插件？

**A**:
```python
plugin_manager.disable_plugin("plugin_name")
```

或在插件配置中设置 `enabled: false`

#### Q14: 插件配置如何保存？

**A**: 插件配置保存在：
- 环境变量
- 配置文件
- 数据库（如需要）

### 性能和部署问题

#### Q15: 系统响应慢怎么办？

**A**:
1. 检查数据库性能（索引、查询优化）
2. 启用缓存（Redis）
3. 优化 API 响应（分页、压缩）
4. 查看性能监控指标

#### Q16: 如何备份数据？

**A**:
```bash
# 备份数据库
docker-compose exec postgres pg_dump -U agentforge agentforge > backup.sql

# 恢复数据库
cat backup.sql | docker-compose exec -T postgres psql -U agentforge agentforge
```

#### Q17: 如何监控系统状态？

**A**:
1. 使用内置监控端点：`GET /api/health`
2. 配置 Prometheus 采集指标
3. 使用 Grafana 仪表板
4. 查看应用日志

#### Q18: 生产环境如何配置 HTTPS？

**A**:
1. 使用 Nginx 反向代理
2. 配置 Let's Encrypt 证书
3. 设置自动更新脚本
4. 强制 HTTPS 重定向

详细配置参考 [部署指南](DEPLOYMENT.md)。

---

## 📚 相关文档

- [部署指南](DEPLOYMENT.md) - 生产环境部署
- [API 文档](http://localhost:8000/docs) - Swagger UI
- [架构文档](architecture/adr.md) - 架构决策记录

---

**最后更新**: 2026-03-30  
**版本**: 1.0.0
