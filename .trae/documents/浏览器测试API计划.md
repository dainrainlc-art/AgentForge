# 浏览器中测试 AgentForge API 计划

## 概述

本计划详细说明如何在浏览器中使用 Swagger UI 测试 AgentForge API。

## 前置条件

- 服务已启动：http://localhost:8000
- 浏览器可访问

---

## 步骤 1：打开 Swagger UI

1. 打开浏览器
2. 访问地址：http://localhost:8000/docs
3. 您将看到 Swagger UI 界面，4. 界面显示所有可用的 API 端点

---

## 步骤 2：测试健康检查 API

### 2.1 展开 `/api/health` 端点

1. 在 Swagger UI 中找到 `/api/health` 端点
2. 点击该端点展开
3. 点击 "Try it out" 按钮
4. 点击 "Execute" 执行请求

### 预期结果

```json
{
  "status": "healthy",
  "timestamp": "2026-03-28T...",
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

---

## 步骤 3：用户注册

### 3.1 展开 `/api/auth/register` 端点

1. 找到 `/api/auth/register` 端点
2. 点击展开
3. 点击 "Try it out"
4. 在请求体中输入：

```json
{
  "email": "mytest@example.com",
  "password": "mypassword123",
  "name": "My Test User"
}
```

5. 点击 "Execute"

### 预期结果

```json
{
  "id": "user_X",
  "email": "mytest@example.com",
  "name": "My Test User",
  "created_at": "2026-03-28T..."
}
```

---

## 步骤 4：用户登录（获取Token）

### 4.1 展开 `/api/auth/login` 端点

1. 找到 `/api/auth/login` 端点
2. 点击展开
3. 点击 "Try it out"
4. 在请求体中输入：

```json
{
  "email": "mytest@example.com",
  "password": "mypassword123"
}
```

5. 点击 "Execute"

### 预期结果

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

### 4.2 复制 Token

**重要**：复制返回的 `access_token` 值，后续步骤需要使用！

---

## 步骤 5：配置认证

### 5.1 打开认证配置

1. 在 Swagger UI 页面右上角找到 "Authorize" 按钮
2. 点击 "Authorize" 按钮
3. 在弹出框中输入：`Bearer YOUR_TOKEN`
   - 将 `YOUR_TOKEN` 替换为步骤4获取的 token
4. 点击 "Authorize"
5. 点击 "Close"

---

## 步骤 6：测试聊天 API

### 6.1 发送聊天消息

1. 找到 `/api/chat/message` 端点
2. 点击展开
3. 点击 "Try it out"
4. 在请求体中输入:

```json
{
  "message": "你好，请介绍一下你自己"
}
```

5. 点击 "Execute"

### 预期结果

```json
{
  "response": "你好！我是GLM，一个由Z.ai训练的大语言模型...",
  "agent_id": "agent_user_X",
  "timestamp": "2026-03-28T...",
  "memories_used": 0
}
```

### 6.2 获取对话历史

1. 找到 `/api/chat/history` 端点
2. 点击展开
3. 点击 "Try it out"
4. 点击 "Execute"

### 预期结果

```json
{
  "messages": [
    {
      "role": "user",
      "content": "你好，请介绍一下你自己",
      "timestamp": "..."
    },
    {
      "role": "assistant",
      "content": "你好！我是GLM...",
      "timestamp": "..."
    }
  ],
  "total": 2
}
```

### 6.3 获取 Agent 状态

1. 找到 `/api/chat/status` 端点
2. 点击展开
3. 点击 "Try it out"
4. 点击 "Execute"

### 预期结果

```json
{
  "agent_id": "agent_user_X",
  "name": "AgentForge-user_X",
  "created_at": "...",
  "conversation_count": 2,
  "status": "active"
}
```

---

## 步骤 7：测试其他 API

### 7.1 获取当前用户信息

1. 找到 `/api/auth/me` 端点
2. 点击展开
3. 点击 "Try it out"
4. 点击 "Execute"

### 预期结果

```json
{
  "id": "user_X",
  "email": "mytest@example.com",
  "name": "My Test User",
  "created_at": "..."
}
```

---

## 常见问题

### Q1: 401 Unauthorized 错误

**原因**：Token 未配置或已过期

**解决**：
1. 重新执行登录获取新 Token
2. 重新配置 Authorize

### Q2: 422 Unprocessable Entity 错误

**原因**：请求参数格式错误

**解决**：
1. 检查 JSON 格式是否正确
2. 确保必填字段都已填写

### Q3: Token 过期

**原因**：Token 有效期为 24 小时

**解决**：
1. 重新登录获取新 Token
2. 更新 Authorize 配置

---

## 测试清单

- [ ] 打开 Swagger UI (http://localhost:8000/docs)
- [ ] 测试健康检查 API
- [ ] 注册新用户
- [ ] 登录获取 Token
- [ ] 配置 Authorize
- [ ] 发送聊天消息
- [ ] 获取对话历史
- [ ] 获取 Agent 状态
- [ ] 获取当前用户信息

---

## 可用模型列表

百度千帆 Coding Plan Pro 支持以下模型：

| 模型名称 | 用途 |
|---------|------|
| `glm-5` | 默认模型，通用对话 |
| `kimi-k2.5` | 长上下文理解 |
| `deepseek-v3.2` | 代码生成 |
| `minimax-m2.5` | 创意写作 |

---

## 注意事项

1. **Token 安全**：不要将 Token 分享给他人
2. **测试数据**：建议使用测试邮箱，不要使用真实邮箱
3. **服务状态**：确保服务正常运行（健康检查返回 healthy）
4. **浏览器兼容**：推荐使用 Chrome 或 Firefox 浏览器
