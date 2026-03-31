# AgentForge API 使用指南

## 概述

AgentForge API 是一个基于 FastAPI 的 RESTful API，提供对 Fiverr 运营自动化、社交媒体营销、知识管理和 AI 能力的编程访问。

## 基础信息

| 属性 | 值 |
|------|-----|
| 基础 URL | `http://localhost:8000` |
| API 文档 | `http://localhost:8000/docs` |
| 健康检查 | `http://localhost:8000/health` |

## 认证

### 获取访问令牌

```bash
curl -X POST "http://localhost:8000/api/v1/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=your_password"
```

响应:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

### 使用令牌

```bash
curl -X GET "http://localhost:8000/api/v1/users/me" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

---

## 用户管理

### 获取当前用户

```bash
curl -X GET "http://localhost:8000/api/v1/users/me" \
  -H "Authorization: Bearer <token>"
```

### 创建用户

```bash
curl -X POST "http://localhost:8000/api/v1/users" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "newuser",
    "email": "user@example.com",
    "password": "securepassword",
    "full_name": "New User"
  }'
```

---

## Fiverr 订单

### 列出订单

```bash
curl -X GET "http://localhost:8000/api/v1/fiverr/orders?status=active&limit=10" \
  -H "Authorization: Bearer <token>"
```

### 获取订单详情

```bash
curl -X GET "http://localhost:8000/api/v1/fiverr/orders/{order_id}" \
  -H "Authorization: Bearer <token>"
```

### 更新订单状态

```bash
curl -X PATCH "http://localhost:8000/api/v1/fiverr/orders/{order_id}/status" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"status": "in_progress"}'
```

### 添加订单备注

```bash
curl -X POST "http://localhost:8000/api/v1/fiverr/orders/{order_id}/notes" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"content": "客户要求提前交付"}'
```

---

## 社交媒体

### 列出社交媒体账号

```bash
curl -X GET "http://localhost:8000/api/v1/social/accounts" \
  -H "Authorization: Bearer <token>"
```

### 创建内容

```bash
curl -X POST "http://localhost:8000/api/v1/social/content" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "twitter",
    "content": "正在开发 AI 驱动的 Fiverr 自动化系统! #AI #Automation",
    "scheduled_time": "2024-12-25T10:00:00Z",
    "media_urls": []
  }'
```

### 获取内容列表

```bash
curl -X GET "http://localhost:8000/api/v1/social/content?platform=twitter&status=draft" \
  -H "Authorization: Bearer <token>"
```

### 发布内容

```bash
curl -X POST "http://localhost:8000/api/v1/social/content/{content_id}/publish" \
  -H "Authorization: Bearer <token>"
```

### 分析内容效果

```bash
curl -X GET "http://localhost:8000/api/v1/social/content/{content_id}/analytics" \
  -H "Authorization: Bearer <token>"
```

---

## AI 能力

### 生成内容

```bash
curl -X POST "http://localhost:8000/api/v1/ai/generate" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "为一个 Fiverr Python 编程服务写一段吸引人的描述",
    "task_type": "content_generation",
    "context": {
      "service_type": "python_development",
      "target_audience": "需要自动化脚本的客户"
    }
  }'
```

### 意图识别

```bash
curl -X POST "http://localhost:8000/api/v1/ai/intent" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "我想自动化我的 Fiverr 订单处理流程"
  }'
```

### 情感分析

```bash
curl -X POST "http://localhost:8000/api/v1/ai/sentiment" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Great service, fast delivery!"
  }'
```

---

## 知识管理

### 创建文档

```bash
curl -X POST "http://localhost:8000/api/v1/knowledge/documents" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Fiverr 服务交付指南",
    "content": "# 交付标准\n\n1. 代码质量\n2. 文档完整性",
    "category": "guides",
    "tags": ["fiverr", "delivery", "guide"]
  }'
```

### 搜索文档

```bash
curl -X GET "http://localhost:8000/api/v1/knowledge/search?q=交付指南&limit=5" \
  -H "Authorization: Bearer <token>"
```

### 获取文档

```bash
curl -X GET "http://localhost:8000/api/v1/knowledge/documents/{doc_id}" \
  -H "Authorization: Bearer <token>"
```

### 更新文档

```bash
curl -X PUT "http://localhost:8000/api/v1/knowledge/documents/{doc_id}" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Fiverr 服务交付指南 (更新版)",
    "content": "# 交付标准\n\n1. 代码质量\n2. 文档完整性\n3. 测试覆盖"
  }'
```

---

## 文件处理

### 上传文件

```bash
curl -X POST "http://localhost:8000/api/v1/files/upload" \
  -H "Authorization: Bearer <token>" \
  -F "file=@/path/to/document.pdf" \
  -F "tags=invoice,2024"
```

### 列出文件

```bash
curl -X GET "http://localhost:8000/api/v1/files?file_type=document&limit=20" \
  -H "Authorization: Bearer <token>"
```

### 下载文件

```bash
curl -X GET "http://localhost:8000/api/v1/files/{file_id}/download" \
  -H "Authorization: Bearer <token>" \
  -o downloaded_file.pdf
```

### 解析文件

```bash
curl -X POST "http://localhost:8000/api/v1/files/{file_id}/parse" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"options": {"extract_tables": true}}'
```

### 删除文件

```bash
curl -X DELETE "http://localhost:8000/api/v1/files/{file_id}" \
  -H "Authorization: Bearer <token>"
```

---

## 插件

### 列出可用插件

```bash
curl -X GET "http://localhost:8000/api/v1/plugins" \
  -H "Authorization: Bearer <token>"
```

### 执行插件

```bash
curl -X POST "http://localhost:8000/api/v1/plugins/weather/query" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "city": "Shanghai",
    "unit": "celsius"
  }'
```

### 货币转换

```bash
curl -X POST "http://localhost:8000/api/v1/plugins/currency/convert" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "from": "USD",
    "to": "CNY",
    "amount": 100
  }'
```

### 日历事件

```bash
curl -X POST "http://localhost:8000/api/v1/plugins/calendar/event" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Fiverr 订单交付",
    "description": "完成 #1234 订单的代码交付",
    "start_time": "2024-12-25T14:00:00Z",
    "end_time": "2024-12-25T16:00:00Z",
    "reminder_minutes": 30
  }'
```

---

## 工作流

### 列出工作流

```bash
curl -X GET "http://localhost:8000/api/v1/workflows" \
  -H "Authorization: Bearer <token>"
```

### 触发工作流

```bash
curl -X POST "http://localhost:8000/api/v1/workflows/{workflow_id}/execute" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "inputs": {
      "order_id": "1234",
      "action": "deliver"
    }
  }'
```

### 获取执行状态

```bash
curl -X GET "http://localhost:8000/api/v1/workflows/executions/{exec_id}" \
  -H "Authorization: Bearer <token>"
```

---

## Webhook

### 列出 Webhook

```bash
curl -X GET "http://localhost:8000/api/v1/webhooks" \
  -H "Authorization: Bearer <token>"
```

### 创建 Webhook

```bash
curl -X POST "http://localhost:8000/api/v1/webhooks" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Order Completed",
    "url": "https://example.com/webhook",
    "events": ["order.completed", "order.cancelled"],
    "secret": "webhook_secret_key"
  }'
```

---

## 错误响应

### 错误格式

```json
{
  "detail": "错误描述信息",
  "code": "ERROR_CODE",
  "timestamp": "2024-12-25T10:00:00Z"
}
```

### 常见错误码

| HTTP 状态码 | 错误码 | 说明 |
|-------------|--------|------|
| 400 | VALIDATION_ERROR | 请求参数验证失败 |
| 401 | UNAUTHORIZED | 未认证或令牌无效 |
| 403 | FORBIDDEN | 无权限访问 |
| 404 | NOT_FOUND | 资源不存在 |
| 429 | RATE_LIMITED | 请求过于频繁 |
| 500 | INTERNAL_ERROR | 服务器内部错误 |

---

## 速率限制

| 端点类型 | 限制 |
|----------|------|
| 普通 API | 100 请求/分钟 |
| AI 生成 | 20 请求/分钟 |
| 文件上传 | 10 请求/分钟 |

---

## Python SDK 示例

```python
import requests

class AgentForgeClient:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {token}"}

    def get_orders(self, status: str = None):
        params = {"status": status} if status else {}
        return requests.get(
            f"{self.base_url}/api/v1/fiverr/orders",
            headers=self.headers,
            params=params
        )

    def create_content(self, platform: str, content: str):
        return requests.post(
            f"{self.base_url}/api/v1/social/content",
            headers=self.headers,
            json={"platform": platform, "content": content}
        )

    def search_knowledge(self, query: str):
        return requests.get(
            f"{self.base_url}/api/v1/knowledge/search",
            headers=self.headers,
            params={"q": query}
        )


# 使用示例
client = AgentForgeClient(
    base_url="http://localhost:8000",
    token="your_access_token"
)

# 获取活跃订单
orders = client.get_orders(status="active")
print(orders.json())

# 创建社交媒体内容
content = client.create_content(
    platform="twitter",
    content="Hello from AgentForge!"
)
print(content.json())

# 搜索知识库
results = client.search_knowledge("Fiverr 指南")
print(results.json())
```

---

## JavaScript/TypeScript SDK 示例

```typescript
class AgentForgeClient {
  private baseUrl: string;
  private headers: Record<string, string>;

  constructor(baseUrl: string, token: string) {
    this.baseUrl = baseUrl;
    this.headers = {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };
  }

  async getOrders(status?: string) {
    const params = status ? `?status=${status}` : '';
    const response = await fetch(
      `${this.baseUrl}/api/v1/fiverr/orders${params}`,
      { headers: this.headers }
    );
    return response.json();
  }

  async createContent(platform: string, content: string) {
    const response = await fetch(
      `${this.baseUrl}/api/v1/social/content`,
      {
        method: 'POST',
        headers: this.headers,
        body: JSON.stringify({ platform, content })
      }
    );
    return response.json();
  }

  async searchKnowledge(query: string) {
    const response = await fetch(
      `${this.baseUrl}/api/v1/knowledge/search?q=${encodeURIComponent(query)}`,
      { headers: this.headers }
    );
    return response.json();
  }
}

// 使用示例
const client = new AgentForgeClient(
  'http://localhost:8000',
  'your_access_token'
);

const orders = await client.getOrders('active');
console.log(orders);

await client.createContent('twitter', 'Hello from AgentForge!');
const results = await client.searchKnowledge('Fiverr 指南');
console.log(results);
```
