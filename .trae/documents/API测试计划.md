# AgentForge API 测试计划

## 概述

AgentForge API 服务已成功启动，本文档提供 API 端点说明和测试方法。

---

## API 端点列表

### 1. 健康检查 API

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/health` | GET | 检查系统健康状态 |
| `/api/health/live` | GET | Kubernetes 存活探针 |
| `/api/health/ready` | GET | Kubernetes 就绪探针 |

### 2. 认证 API

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/auth/register` | POST | 用户注册 |
| `/api/auth/login` | POST | 用户登录（获取JWT Token） |
| `/api/auth/me` | GET | 获取当前用户信息（需要认证） |

### 3. 聊天 API

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/chat/message` | POST | 发送消息给Agent（需要认证） |
| `/api/chat/history` | GET | 获取对话历史（需要认证） |
| `/api/chat/status` | GET | 获取Agent状态（需要认证） |

---

## 测试步骤

### 步骤 1：检查服务状态

```bash
curl -s http://localhost:8000/api/health | python3 -m json.tool
```

**预期结果**：
```json
{
    "status": "healthy",
    "timestamp": "...",
    "version": "1.0.0",
    "services": {
        "llm": {"status": "healthy", "provider": "baidu_qianfan"},
        "memory": {"status": "healthy", "redis": true, "qdrant": true}
    }
}
```

### 步骤 2：用户注册

```bash
curl -s -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "test123", "name": "Test User"}' | python3 -m json.tool
```

**预期结果**：
```json
{
    "id": "user_1",
    "email": "test@example.com",
    "name": "Test User",
    "created_at": "..."
}
```

### 步骤 3：用户登录（获取Token）

```bash
curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "test123"}' | python3 -m json.tool
```

**预期结果**：
```json
{
    "access_token": "eyJ...",
    "token_type": "bearer",
    "expires_in": 86400
}
```

### 步骤 4：发送聊天消息

```bash
# 替换 YOUR_TOKEN 为步骤3获取的access_token
curl -s -X POST http://localhost:8000/api/chat/message \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"message": "你好，请介绍一下你自己"}' | python3 -m json.tool
```

**预期结果**：
```json
{
    "response": "你好！我是AgentForge...",
    "agent_id": "agent_user_1",
    "timestamp": "...",
    "memories_used": 0
}
```

### 步骤 5：获取对话历史

```bash
curl -s http://localhost:8000/api/chat/history \
  -H "Authorization: Bearer YOUR_TOKEN" | python3 -m json.tool
```

### 步骤 6：获取Agent状态

```bash
curl -s http://localhost:8000/api/chat/status \
  -H "Authorization: Bearer YOUR_TOKEN" | python3 -m json.tool
```

---

## 快速测试脚本

创建一个测试脚本 `test_api.sh`：

```bash
#!/bin/bash

echo "=== 1. 健康检查 ==="
curl -s http://localhost:8000/api/health | python3 -m json.tool

echo -e "\n=== 2. 用户注册 ==="
curl -s -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "test123", "name": "Test User"}' | python3 -m json.tool

echo -e "\n=== 3. 用户登录 ==="
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "test123"}' | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

echo "Token: $TOKEN"

echo -e "\n=== 4. 发送聊天消息 ==="
curl -s -X POST http://localhost:8000/api/chat/message \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"message": "你好，请介绍一下你自己"}' | python3 -m json.tool

echo -e "\n=== 5. 获取对话历史 ==="
curl -s http://localhost:8000/api/chat/history \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

echo -e "\n=== 测试完成 ==="
```

---

## 访问 Swagger UI

在浏览器中访问：**http://localhost:8000/docs**

Swagger UI 提供可视化界面，可以直接测试所有 API：
1. 点击任意 API 端点
2. 点击 "Try it out"
3. 填写参数
4. 点击 "Execute" 执行请求

---

## 注意事项

1. **认证要求**：聊天API需要在请求头中携带 `Authorization: Bearer YOUR_TOKEN`
2. **Token 获取**：先执行注册，再执行登录获取 Token
3. **Token 有效期**：默认 24 小时（86400 秒）
4. **LLM 模型**：默认使用 `glm-5`，支持切换为 `kimi-k2.5`、`deepseek-v3.2`、`minimax-m2.5`
