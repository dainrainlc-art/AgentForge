# AgentForge API 文档模板

本文档定义了AgentForge API的设计规范、请求/响应格式、错误码定义和认证机制。

## 1. API设计规范

### 1.1 RESTful设计原则

AgentForge API遵循RESTful设计原则：

- **资源导向**：URL表示资源，使用名词而非动词
- **HTTP方法语义**：正确使用GET、POST、PUT、DELETE等方法
- **无状态**：每个请求包含所有必要信息
- **统一接口**：一致的URL结构和响应格式

### 1.2 基础URL

```
开发环境: http://localhost:8000/api/v1
生产环境: https://api.agentforge.com/api/v1
```

### 1.3 URL命名规范

| 规则 | 示例 | 说明 |
|------|------|------|
| 使用小写 | `/api/v1/orders` | 全部小写 |
| 使用连字符 | `/api/v1/order-items` | 多词用连字符连接 |
| 使用复数 | `/api/v1/orders` | 资源使用复数形式 |
| 避免嵌套过深 | `/api/v1/orders/{id}/items` | 最多2-3层嵌套 |

### 1.4 HTTP方法使用

| 方法 | 用途 | 幂等性 | 示例 |
|------|------|--------|------|
| GET | 获取资源 | 是 | `GET /orders` |
| POST | 创建资源 | 否 | `POST /orders` |
| PUT | 全量更新 | 是 | `PUT /orders/{id}` |
| PATCH | 部分更新 | 是 | `PATCH /orders/{id}` |
| DELETE | 删除资源 | 是 | `DELETE /orders/{id}` |

## 2. 请求/响应格式

### 2.1 请求头

```http
Content-Type: application/json
Accept: application/json
Authorization: Bearer <access_token>
X-Request-ID: <uuid>
X-API-Version: v1
```

### 2.2 成功响应格式

#### 2.2.1 单资源响应

```json
{
  "success": true,
  "data": {
    "id": "order_123",
    "customer_name": "John Doe",
    "status": "pending",
    "created_at": "2026-03-26T10:00:00Z",
    "updated_at": "2026-03-26T10:00:00Z"
  },
  "error": null,
  "metadata": {
    "timestamp": "2026-03-26T10:00:00Z",
    "request_id": "550e8400-e29b-41d4-a716-446655440000",
    "version": "v1"
  }
}
```

#### 2.2.2 列表响应

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "order_123",
        "customer_name": "John Doe",
        "status": "pending"
      },
      {
        "id": "order_124",
        "customer_name": "Jane Smith",
        "status": "completed"
      }
    ],
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total_items": 100,
      "total_pages": 5,
      "has_next": true,
      "has_prev": false
    }
  },
  "error": null,
  "metadata": {
    "timestamp": "2026-03-26T10:00:00Z",
    "request_id": "550e8400-e29b-41d4-a716-446655440000",
    "version": "v1"
  }
}
```

#### 2.2.3 创建响应

```json
{
  "success": true,
  "data": {
    "id": "order_125",
    "customer_name": "New Customer",
    "status": "pending",
    "created_at": "2026-03-26T10:00:00Z"
  },
  "error": null,
  "metadata": {
    "timestamp": "2026-03-26T10:00:00Z",
    "request_id": "550e8400-e29b-41d4-a716-446655440000",
    "version": "v1"
  }
}
```

### 2.3 错误响应格式

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "请求参数验证失败",
    "details": {
      "field": "customer_name",
      "reason": "客户名称不能为空"
    },
    "suggestion": "请提供有效的客户名称"
  },
  "metadata": {
    "timestamp": "2026-03-26T10:00:00Z",
    "request_id": "550e8400-e29b-41d4-a716-446655440000",
    "version": "v1"
  }
}
```

### 2.4 分页参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| page | integer | 1 | 页码 |
| page_size | integer | 20 | 每页数量（最大100） |
| sort_by | string | created_at | 排序字段 |
| sort_order | string | desc | 排序方向（asc/desc） |

**示例请求**：
```
GET /api/v1/orders?page=2&page_size=50&sort_by=created_at&sort_order=desc
```

### 2.5 过滤参数

```
GET /api/v1/orders?status=pending&customer_id=customer_123
GET /api/v1/orders?created_at_gte=2026-01-01&created_at_lte=2026-03-31
```

## 3. 错误码定义

### 3.1 HTTP状态码

| 状态码 | 说明 | 使用场景 |
|--------|------|----------|
| 200 | OK | 成功响应 |
| 201 | Created | 资源创建成功 |
| 204 | No Content | 删除成功（无返回体） |
| 400 | Bad Request | 请求参数错误 |
| 401 | Unauthorized | 未认证 |
| 403 | Forbidden | 无权限 |
| 404 | Not Found | 资源不存在 |
| 409 | Conflict | 资源冲突 |
| 422 | Unprocessable Entity | 语义错误 |
| 429 | Too Many Requests | 请求过于频繁 |
| 500 | Internal Server Error | 服务器内部错误 |
| 502 | Bad Gateway | 上游服务错误 |
| 503 | Service Unavailable | 服务不可用 |

### 3.2 业务错误码

#### 3.2.1 通用错误码 (1xxx)

| 错误码 | HTTP状态码 | 说明 | 建议 |
|--------|------------|------|------|
| SUCCESS | 200 | 成功 | - |
| BAD_REQUEST | 400 | 请求参数错误 | 检查请求参数 |
| UNAUTHORIZED | 401 | 未授权 | 提供有效的认证信息 |
| FORBIDDEN | 403 | 禁止访问 | 检查用户权限 |
| NOT_FOUND | 404 | 资源不存在 | 检查资源ID |
| CONFLICT | 409 | 资源冲突 | 检查资源状态 |
| RATE_LIMITED | 429 | 请求过于频繁 | 降低请求频率 |
| INTERNAL_ERROR | 500 | 服务器内部错误 | 联系技术支持 |
| SERVICE_UNAVAILABLE | 503 | 服务不可用 | 稍后重试 |

#### 3.2.2 认证错误码 (2xxx)

| 错误码 | HTTP状态码 | 说明 | 建议 |
|--------|------------|------|------|
| AUTH_INVALID_TOKEN | 401 | 无效的令牌 | 重新登录 |
| AUTH_EXPIRED_TOKEN | 401 | 令牌已过期 | 刷新令牌 |
| AUTH_INVALID_CREDENTIALS | 401 | 凭据无效 | 检查用户名密码 |
| AUTH_ACCOUNT_LOCKED | 403 | 账户已锁定 | 联系管理员 |
| AUTH_PERMISSION_DENIED | 403 | 权限不足 | 申请相应权限 |

#### 3.2.3 业务错误码 (3xxx)

| 错误码 | HTTP状态码 | 说明 | 建议 |
|--------|------------|------|------|
| ORDER_NOT_FOUND | 404 | 订单不存在 | 检查订单ID |
| ORDER_STATUS_INVALID | 400 | 订单状态无效 | 检查订单状态 |
| CUSTOMER_NOT_FOUND | 404 | 客户不存在 | 检查客户ID |
| CONTENT_GENERATION_FAILED | 500 | 内容生成失败 | 重试或联系支持 |

#### 3.2.4 AI服务错误码 (4xxx)

| 错误码 | HTTP状态码 | 说明 | 建议 |
|--------|------------|------|------|
| LLM_ERROR | 500 | LLM调用错误 | 重试或联系支持 |
| LLM_TIMEOUT | 504 | LLM调用超时 | 稍后重试 |
| QUOTA_EXCEEDED | 429 | 配额超限 | 等待配额重置 |
| MODEL_UNAVAILABLE | 503 | 模型不可用 | 稍后重试 |
| EMBEDDING_ERROR | 500 | 向量嵌入错误 | 检查输入内容 |

#### 3.2.5 工作流错误码 (5xxx)

| 错误码 | HTTP状态码 | 说明 | 建议 |
|--------|------------|------|------|
| WORKFLOW_ERROR | 500 | 工作流执行错误 | 检查工作流配置 |
| WORKFLOW_TIMEOUT | 504 | 工作流执行超时 | 检查工作流复杂度 |
| WORKFLOW_NOT_FOUND | 404 | 工作流不存在 | 检查工作流ID |
| TRIGGER_ERROR | 500 | 触发器错误 | 检查触发器配置 |

### 3.3 错误响应示例

#### 3.3.1 验证错误

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "请求参数验证失败",
    "details": {
      "errors": [
        {
          "field": "email",
          "message": "无效的邮箱格式"
        },
        {
          "field": "phone",
          "message": "手机号格式不正确"
        }
      ]
    },
    "suggestion": "请检查并修正请求参数"
  },
  "metadata": {
    "timestamp": "2026-03-26T10:00:00Z",
    "request_id": "550e8400-e29b-41d4-a716-446655440000",
    "version": "v1"
  }
}
```

#### 3.3.2 业务错误

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "ORDER_STATUS_INVALID",
    "message": "订单状态不允许此操作",
    "details": {
      "order_id": "order_123",
      "current_status": "completed",
      "allowed_transitions": ["cancelled"]
    },
    "suggestion": "只能取消已完成的订单"
  },
  "metadata": {
    "timestamp": "2026-03-26T10:00:00Z",
    "request_id": "550e8400-e29b-41d4-a716-446655440000",
    "version": "v1"
  }
}
```

## 4. 认证机制

### 4.1 认证方式

AgentForge API支持以下认证方式：

| 认证方式 | 适用场景 | 说明 |
|----------|----------|------|
| Bearer Token | API调用 | JWT令牌认证 |
| API Key | 服务间调用 | 长期有效的密钥 |
| OAuth 2.0 | 第三方集成 | 授权码流程 |

### 4.2 Bearer Token认证

#### 4.2.1 获取令牌

**请求**：
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "your_password"
}
```

**响应**：
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "Bearer",
    "expires_in": 3600
  },
  "error": null,
  "metadata": {
    "timestamp": "2026-03-26T10:00:00Z",
    "request_id": "550e8400-e29b-41d4-a716-446655440000",
    "version": "v1"
  }
}
```

#### 4.2.2 使用令牌

```http
GET /api/v1/orders
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### 4.2.3 刷新令牌

```http
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### 4.3 API Key认证

适用于服务间调用：

```http
GET /api/v1/orders
X-API-Key: your_api_key_here
```

### 4.4 JWT令牌结构

```json
{
  "header": {
    "alg": "HS256",
    "typ": "JWT"
  },
  "payload": {
    "sub": "user_123",
    "iat": 1679817600,
    "exp": 1679821200,
    "role": "admin",
    "permissions": ["read:orders", "write:orders"]
  },
  "signature": "..."
}
```

### 4.5 权限控制

#### 4.5.1 角色定义

| 角色 | 权限 |
|------|------|
| admin | 所有权限 |
| operator | 订单管理、内容管理 |
| viewer | 只读权限 |

#### 4.5.2 权限检查

```http
GET /api/v1/admin/users
Authorization: Bearer <token>

Response (403 Forbidden):
{
  "success": false,
  "error": {
    "code": "AUTH_PERMISSION_DENIED",
    "message": "权限不足",
    "details": {
      "required_permission": "admin:users",
      "current_permissions": ["read:orders"]
    }
  }
}
```

## 5. API端点模板

### 5.1 订单管理API

#### 获取订单列表

```http
GET /api/v1/orders
Authorization: Bearer <token>
```

**查询参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| status | string | 否 | 订单状态过滤 |
| customer_id | string | 否 | 客户ID过滤 |
| page | integer | 否 | 页码 |
| page_size | integer | 否 | 每页数量 |

**响应**：
```json
{
  "success": true,
  "data": {
    "items": [...],
    "pagination": {...}
  }
}
```

#### 创建订单

```http
POST /api/v1/orders
Authorization: Bearer <token>
Content-Type: application/json

{
  "customer_id": "customer_123",
  "service_type": "pcb_design",
  "description": "PCB设计项目",
  "budget": 500.00,
  "deadline": "2026-04-15"
}
```

#### 获取订单详情

```http
GET /api/v1/orders/{order_id}
Authorization: Bearer <token>
```

#### 更新订单

```http
PUT /api/v1/orders/{order_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "status": "in_progress",
  "notes": "开始处理"
}
```

#### 删除订单

```http
DELETE /api/v1/orders/{order_id}
Authorization: Bearer <token>
```

### 5.2 内容管理API

#### 生成内容

```http
POST /api/v1/content/generate
Authorization: Bearer <token>
Content-Type: application/json

{
  "type": "blog_post",
  "topic": "医疗器械固件开发最佳实践",
  "style": "professional",
  "length": "medium",
  "language": "zh-CN"
}
```

#### 发布内容

```http
POST /api/v1/content/publish
Authorization: Bearer <token>
Content-Type: application/json

{
  "content_id": "content_123",
  "platforms": ["linkedin", "twitter"],
  "scheduled_at": "2026-03-27T10:00:00Z"
}
```

### 5.3 知识库API

#### 搜索知识

```http
GET /api/v1/knowledge/search?q=PCB设计规范&limit=10
Authorization: Bearer <token>
```

#### 同步知识库

```http
POST /api/v1/knowledge/sync
Authorization: Bearer <token>
Content-Type: application/json

{
  "source": "obsidian",
  "force": false
}
```

## 6. 速率限制

### 6.1 限制规则

| 端点类型 | 限制 | 窗口 |
|----------|------|------|
| 普通API | 100次 | 1分钟 |
| AI生成API | 20次 | 1分钟 |
| 认证API | 10次 | 1分钟 |

### 6.2 响应头

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1679821200
```

### 6.3 超限响应

```http
HTTP/1.1 429 Too Many Requests
Content-Type: application/json

{
  "success": false,
  "error": {
    "code": "RATE_LIMITED",
    "message": "请求过于频繁",
    "details": {
      "limit": 100,
      "remaining": 0,
      "reset_at": "2026-03-26T10:05:00Z"
    },
    "suggestion": "请在60秒后重试"
  }
}
```

## 7. Webhook规范

### 7.1 Webhook端点

```http
POST /webhook/{source}
Content-Type: application/json
X-Webhook-Signature: sha256=<signature>
```

### 7.2 签名验证

```python
import hmac
import hashlib

def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    expected = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)
```

### 7.3 事件类型

| 事件 | 描述 |
|------|------|
| order.created | 新订单创建 |
| order.updated | 订单状态更新 |
| order.completed | 订单完成 |
| message.received | 收到新消息 |
| content.published | 内容发布完成 |
| task.completed | 任务完成 |

## 8. 相关文档

- [架构概览](../architecture/overview.md)
- [API规范设计](../architecture/api-specification.md)
- [开发指南](../guides/development.md)
