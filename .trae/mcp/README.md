# AgentForge MCP Servers 配置文档

## 概述

AgentForge 使用 MCP (Model Context Protocol) Servers 来扩展 AI Agent 的能力。本文档详细说明了各 MCP Server 的功能、配置方法和使用示例。

## MCP Servers 列表

### 1. Filesystem (文件系统)

**功能说明**
- 提供文件系统读写操作能力
- 支持创建、读取、更新、删除文件和目录
- 支持文件搜索和路径操作

**配置方法**
```json
{
  "filesystem": {
    "command": "mcp-server-filesystem",
    "args": ["/home/dainrain4/trae_projects/AgentForge"],
    "description": "文件系统操作，支持读写项目文件",
    "enabled": true,
    "priority": "high"
  }
}
```

**使用示例**
```
# 读取文件
read_file("/home/dainrain4/trae_projects/AgentForge/README.md")

# 写入文件
write_file("/home/dainrain4/trae_projects/AgentForge/test.txt", "Hello World")

# 列出目录
list_directory("/home/dainrain4/trae_projects/AgentForge/src")

# 搜索文件
search_files("*.py")
```

**故障排除**
- **权限错误**: 确保运行进程的用户对目标目录有读写权限
- **路径不存在**: 检查 `args` 中的路径是否正确
- **命令未找到**: 安装 `mcp-server-filesystem` 包

---

### 2. GitHub

**功能说明**
- GitHub API 集成
- 支持 Issues、Pull Requests、代码仓库操作
- 支持代码搜索和仓库管理

**配置方法**
```json
{
  "github": {
    "command": "mcp-server-github",
    "args": [],
    "env": {
      "GITHUB_TOKEN": "${GITHUB_TOKEN}"
    },
    "description": "GitHub仓库管理，支持Issues、PR、代码操作",
    "enabled": true,
    "priority": "high"
  }
}
```

**环境变量设置**
```bash
# 在 ~/.bashrc 或 ~/.zshrc 中添加
export GITHUB_TOKEN="your_github_personal_access_token"
```

**获取 GitHub Token**
1. 访问 https://github.com/settings/tokens
2. 点击 "Generate new token (classic)"
3. 选择所需权限（repo, read:org 等）
4. 生成并保存 token

**使用示例**
```
# 创建 Issue
create_issue(owner="username", repo="repo-name", title="Bug report", body="Description")

# 列出 Pull Requests
list_pull_requests(owner="username", repo="repo-name", state="open")

# 搜索代码
search_code(query="function language:python repo:username/repo-name")

# 获取文件内容
get_file_contents(owner="username", repo="repo-name", path="src/main.py")
```

**故障排除**
- **认证失败**: 检查 GITHUB_TOKEN 是否正确设置
- **权限不足**: 确保 token 有足够的权限（repo, read:org 等）
- **API 限流**: GitHub API 有速率限制，等待后重试

---

### 3. PostgreSQL

**功能说明**
- PostgreSQL 数据库操作
- 支持查询、插入、更新、删除操作
- 支持事务和复杂查询

**配置方法**
```json
{
  "postgres": {
    "command": "mcp-server-postgres",
    "args": [],
    "env": {
      "DATABASE_URL": "postgresql://agentforge:${POSTGRES_PASSWORD}@localhost:5432/agentforge"
    },
    "description": "PostgreSQL数据库操作",
    "enabled": true,
    "priority": "high"
  }
}
```

**环境变量设置**
```bash
export POSTGRES_PASSWORD="your_secure_password"
```

**数据库准备**
```bash
# 创建数据库
sudo -u postgres createdb agentforge

# 创建用户
sudo -u postgres psql -c "CREATE USER agentforge WITH PASSWORD 'your_password';"

# 授权
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE agentforge TO agentforge;"
```

**使用示例**
```sql
-- 查询数据
SELECT * FROM users WHERE id = 1;

-- 插入数据
INSERT INTO users (name, email) VALUES ('John', 'john@example.com');

-- 更新数据
UPDATE users SET name = 'Jane' WHERE id = 1;

-- 删除数据
DELETE FROM users WHERE id = 1;
```

**故障排除**
- **连接失败**: 检查 PostgreSQL 服务是否运行 (`sudo systemctl status postgresql`)
- **认证错误**: 验证用户名、密码和数据库名称
- **权限错误**: 确保用户有足够的数据库权限
- **端口错误**: 默认端口为 5432，检查是否被占用

---

### 4. Redis

**功能说明**
- Redis 缓存操作
- 支持键值存储、列表、集合、哈希等数据结构
- 支持过期时间和缓存策略

**配置方法**
```json
{
  "redis": {
    "command": "mcp-server-redis",
    "args": [],
    "env": {
      "REDIS_URL": "redis://localhost:6379"
    },
    "description": "Redis缓存操作",
    "enabled": true,
    "priority": "medium"
  }
}
```

**Redis 安装与启动**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server

# 验证运行状态
redis-cli ping
# 应返回: PONG
```

**使用示例**
```bash
# 设置键值
SET user:1:name "John"

# 获取值
GET user:1:name

# 设置带过期时间的键
SETEX session:abc 3600 "user_data"

# 哈希操作
HSET user:1 name "John" email "john@example.com"
HGET user:1 name

# 列表操作
LPUSH tasks "task1" "task2"
RPOP tasks

# 集合操作
SADD tags "python" "redis" "mcp"
SMEMBERS tags
```

**故障排除**
- **连接被拒绝**: 检查 Redis 服务状态 (`sudo systemctl status redis-server`)
- **内存不足**: 检查 Redis 内存配置 (`redis-cli CONFIG GET maxmemory`)
- **持久化错误**: 检查 Redis 日志 (`/var/log/redis/redis-server.log`)

---

### 5. Web Search (网络搜索)

**功能说明**
- 网络搜索能力
- 支持信息检索和网页抓取
- 支持多种搜索引擎

**配置方法**
```json
{
  "web-search": {
    "command": "mcp-server-web-search",
    "args": [],
    "description": "网络搜索能力，支持信息检索",
    "enabled": true,
    "priority": "medium"
  }
}
```

**环境变量设置**（可选）
```bash
# 如果使用特定搜索 API
export SEARCH_API_KEY="your_api_key"
```

**使用示例**
```
# 基础搜索
search("Python tutorial")

# 高级搜索
search("machine learning site:github.com")

# 新闻搜索
search_news("AI latest developments")

# 图片搜索
search_images("landscape photography")
```

**故障排除**
- **搜索失败**: 检查网络连接
- **API 限制**: 如果使用付费 API，检查配额和计费
- **结果为空**: 调整搜索关键词或检查搜索语法

---

## Agent 与 MCP Server 映射

不同类型的 Agent 使用不同的 MCP Servers：

| Agent 类型 | 可用的 MCP Servers |
|-----------|-------------------|
| Architect | filesystem, github |
| AI Engineer | filesystem, github, web-search |
| Software Engineer | filesystem, github, postgres, redis |
| Frontend Engineer | filesystem, github |
| Security Engineer | filesystem, github, postgres |
| Network Engineer | filesystem, github, web-search |
| Psychologist | filesystem, web-search |
| Anthropologist | filesystem, web-search |
| Test Engineer | filesystem, github, postgres |

---

## 全局配置

```json
{
  "mcpConfig": {
    "version": "1.0",
    "description": "AgentForge MCP Servers配置",
    "globalTimeout": 30000,
    "retryPolicy": {
      "maxRetries": 3,
      "backoffMultiplier": 2,
      "initialDelay": 1000
    }
  }
}
```

**配置说明**
- `globalTimeout`: 全局超时时间（毫秒），默认 30 秒
- `maxRetries`: 最大重试次数，默认 3 次
- `backoffMultiplier`: 退避乘数，用于计算重试间隔
- `initialDelay`: 初始延迟时间（毫秒）

---

## 安装 MCP Servers

### 使用 npm 安装
```bash
# Filesystem
npm install -g @modelcontextprotocol/server-filesystem

# GitHub
npm install -g @modelcontextprotocol/server-github

# PostgreSQL
npm install -g @modelcontextprotocol/server-postgres

# Redis
npm install -g @modelcontextprotocol/server-redis

# Web Search
npm install -g @modelcontextprotocol/server-web-search
```

### 使用 pip 安装（Python 版本）
```bash
pip install mcp-server-filesystem
pip install mcp-server-github
pip install mcp-server-postgres
pip install mcp-server-redis
pip install mcp-server-web-search
```

---

## 安全建议

1. **环境变量管理**
   - 不要在配置文件中硬编码敏感信息
   - 使用 `.env` 文件管理环境变量
   - 将 `.env` 添加到 `.gitignore`

2. **权限控制**
   - 为每个服务使用最小必要权限
   - 定期轮换 API tokens 和密码
   - 限制数据库用户的权限范围

3. **网络安全**
   - 使用 SSL/TLS 加密数据库连接
   - 限制 Redis 只监听本地连接
   - 使用防火墙规则限制访问

4. **日志审计**
   - 启用操作日志记录
   - 定期检查异常访问
   - 监控 API 使用情况

---

## 常见问题

### Q: MCP Server 启动失败怎么办？
A: 
1. 检查命令是否正确安装
2. 查看错误日志
3. 验证环境变量是否设置
4. 检查端口是否被占用

### Q: 如何调试 MCP Server？
A: 
1. 启用详细日志模式
2. 使用独立终端手动启动 server
3. 检查输入输出格式
4. 验证配置文件语法

### Q: 多个 Agent 如何共享 MCP Server？
A: 
MCP Server 支持并发连接，多个 Agent 可以同时使用同一个 Server 实例。配置中的 `agentMcpMapping` 定义了每个 Agent 可访问的 Servers。

### Q: 如何添加新的 MCP Server？
A: 
1. 在 `mcp_config.json` 的 `mcpServers` 中添加配置
2. 在 `agentMcpMapping` 中为需要的 Agent 添加映射
3. 重启 AgentForge 服务

---

## 更新日志

- **2026-03-28**: 初始版本，包含 5 个核心 MCP Servers
