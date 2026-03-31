# AgentForge 接口规范设计

## 1. 内部API规范

### 1.1 RESTful API设计规范

**基础URL**: `http://localhost:8080/api/v1`

**请求格式**:
```http
Content-Type: application/json
Authorization: Bearer <token>
X-Request-ID: <uuid>
```

**响应格式**:
```json
{
  "success": true,
  "data": {},
  "error": null,
  "metadata": {
    "timestamp": "2026-03-26T10:00:00Z",
    "request_id": "uuid",
    "version": "v1"
  }
}
```

**错误响应格式**:
```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable error message",
    "details": {},
    "suggestion": "Suggested action to resolve"
  },
  "metadata": {
    "timestamp": "2026-03-26T10:00:00Z",
    "request_id": "uuid",
    "version": "v1"
  }
}
```

### 1.2 API端点设计

**订单管理API**:
```
GET    /api/v1/orders                 # 获取订单列表
GET    /api/v1/orders/:id             # 获取订单详情
POST   /api/v1/orders                 # 创建订单
PUT    /api/v1/orders/:id             # 更新订单
DELETE /api/v1/orders/:id             # 删除订单
POST   /api/v1/orders/:id/deliver     # 交付订单
```

**客户管理API**:
```
GET    /api/v1/customers              # 获取客户列表
GET    /api/v1/customers/:id          # 获取客户详情
POST   /api/v1/customers              # 创建客户
PUT    /api/v1/customers/:id          # 更新客户
GET    /api/v1/customers/:id/orders   # 获取客户订单
```

**内容管理API**:
```
POST   /api/v1/content/generate       # 生成内容
POST   /api/v1/content/review         # 提交审核
POST   /api/v1/content/publish        # 发布内容
GET    /api/v1/content/scheduled      # 获取计划发布
```

**知识库API**:
```
GET    /api/v1/knowledge/search       # 搜索知识
POST   /api/v1/knowledge/sync         # 同步知识库
GET    /api/v1/knowledge/documents    # 获取文档列表
POST   /api/v1/knowledge/documents    # 创建文档
```

### 1.3 错误码定义

| 错误码 | HTTP状态码 | 描述 |
|--------|-----------|------|
| SUCCESS | 200 | 成功 |
| CREATED | 201 | 创建成功 |
| BAD_REQUEST | 400 | 请求参数错误 |
| UNAUTHORIZED | 401 | 未授权 |
| FORBIDDEN | 403 | 禁止访问 |
| NOT_FOUND | 404 | 资源不存在 |
| CONFLICT | 409 | 资源冲突 |
| RATE_LIMITED | 429 | 请求过于频繁 |
| INTERNAL_ERROR | 500 | 服务器内部错误 |
| SERVICE_UNAVAILABLE | 503 | 服务不可用 |
| LLM_ERROR | 1001 | LLM调用错误 |
| QUOTA_EXCEEDED | 1002 | 配额超限 |
| WORKFLOW_ERROR | 1003 | 工作流执行错误 |

### 1.4 API版本控制

**版本策略**: URL路径版本控制

```
/api/v1/...  # 当前版本
/api/v2/...  # 未来版本
```

**版本兼容规则**:
- 新增字段: 向后兼容
- 删除字段: 需要版本升级
- 修改字段: 需要版本升级
- 废弃API: 提前3个月通知

## 2. Agent间通信协议

### 2.1 消息格式规范

**基础消息结构**:
```json
{
  "message_id": "uuid",
  "timestamp": "2026-03-26T10:00:00Z",
  "source": {
    "agent_id": "architect",
    "agent_type": "architect"
  },
  "target": {
    "agent_id": "ai_engineer",
    "agent_type": "ai_engineer"
  },
  "message_type": "request|response|notification|error",
  "priority": "high|medium|low",
  "correlation_id": "uuid",
  "payload": {
    "action": "action_name",
    "data": {},
    "context": {}
  },
  "metadata": {
    "ttl": 3600,
    "retry_count": 0,
    "requires_response": true
  }
}
```

### 2.2 消息类型定义

**请求消息 (request)**:
```json
{
  "message_type": "request",
  "payload": {
    "action": "generate_content",
    "data": {
      "topic": "医疗器械固件开发",
      "platform": "linkedin",
      "style": "professional"
    },
    "context": {
      "task_id": "task_123",
      "user_preferences": {}
    }
  }
}
```

**响应消息 (response)**:
```json
{
  "message_type": "response",
  "payload": {
    "action": "generate_content",
    "status": "success|failure",
    "data": {
      "content": "生成的内容...",
      "metadata": {}
    },
    "error": null
  }
}
```

**通知消息 (notification)**:
```json
{
  "message_type": "notification",
  "payload": {
    "event": "task_completed",
    "data": {
      "task_id": "task_123",
      "result": {}
    }
  }
}
```

### 2.3 异步通信机制

**消息队列模式**:
```
Producer → Queue → Consumer
         ↓
      Exchange
         ↓
      Routing
```

**队列配置**:
```yaml
queues:
  - name: agent_tasks
    type: direct
    durable: true
    auto_delete: false
    
  - name: agent_notifications
    type: fanout
    durable: true
    
  - name: agent_errors
    type: direct
    durable: true
```

### 2.4 超时与重试策略

**超时配置**:
| 操作类型 | 超时时间 | 说明 |
|----------|----------|------|
| 同步请求 | 30秒 | 需要立即响应 |
| 异步任务 | 5分钟 | 后台执行任务 |
| LLM调用 | 60秒 | AI模型调用 |
| 工作流执行 | 10分钟 | 复杂工作流 |

**重试策略**:
```python
RETRY_CONFIG = {
    "max_retries": 3,
    "initial_delay": 1,  # 秒
    "max_delay": 30,     # 秒
    "backoff_multiplier": 2,
    "retryable_errors": [
        "TIMEOUT",
        "RATE_LIMITED",
        "SERVICE_UNAVAILABLE"
    ]
}
```

### 2.5 状态追踪机制

**任务状态流转**:
```
pending → in_progress → completed
                    ↘ failed
                    ↘ cancelled
```

**状态追踪数据结构**:
```json
{
  "task_id": "uuid",
  "status": "in_progress",
  "progress": 50,
  "started_at": "2026-03-26T10:00:00Z",
  "updated_at": "2026-03-26T10:05:00Z",
  "estimated_completion": "2026-03-26T10:10:00Z",
  "steps": [
    {
      "step_id": "step_1",
      "name": "内容生成",
      "status": "completed",
      "completed_at": "2026-03-26T10:02:00Z"
    },
    {
      "step_id": "step_2",
      "name": "内容审核",
      "status": "in_progress"
    }
  ]
}
```

## 3. 外部API集成规范

### 3.1 Fiverr API集成

**认证方式**: API Key

```python
class FiverrAPIClient:
    BASE_URL = "https://api.fiverr.com/v2"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = httpx.Client()
    
    async def get_orders(self, status: str = None) -> List[Order]:
        """获取订单列表"""
        headers = {"X-API-Key": self.api_key}
        params = {"status": status} if status else {}
        response = await self.session.get(
            f"{self.BASE_URL}/orders",
            headers=headers,
            params=params
        )
        return response.json()
```

### 3.2 社交媒体API集成

**YouTube API**:
```python
class YouTubeAPIClient:
    SCOPES = [
        "https://www.googleapis.com/auth/youtube.upload",
        "https://www.googleapis.com/auth/youtube"
    ]
    
    async def upload_video(
        self,
        video_path: str,
        title: str,
        description: str,
        tags: List[str]
    ) -> str:
        """上传视频"""
        pass
```

**Twitter API**:
```python
class TwitterAPIClient:
    async def post_tweet(
        self,
        text: str,
        media_ids: List[str] = None
    ) -> str:
        """发布推文"""
        pass
    
    async def post_thread(
        self,
        tweets: List[str]
    ) -> List[str]:
        """发布推文线程"""
        pass
```

### 3.3 GitHub API集成

```python
class GitHubAPIClient:
    async def create_repository(
        self,
        name: str,
        description: str,
        private: bool = True
    ) -> dict:
        """创建仓库"""
        pass
    
    async def push_files(
        self,
        repo: str,
        files: List[dict],
        message: str
    ) -> dict:
        """推送文件"""
        pass
```

### 3.4 Notion/Obsidian集成

**Notion API**:
```python
class NotionAPIClient:
    async def create_page(
        self,
        database_id: str,
        properties: dict,
        content: List[dict]
    ) -> dict:
        """创建页面"""
        pass
    
    async def update_page(
        self,
        page_id: str,
        properties: dict
    ) -> dict:
        """更新页面"""
        pass
```

**Obsidian集成**:
```python
class ObsidianClient:
    def __init__(self, vault_path: str):
        self.vault_path = vault_path
    
    async def create_note(
        self,
        title: str,
        content: str,
        folder: str = None
    ) -> str:
        """创建笔记"""
        file_path = self.vault_path / folder / f"{title}.md"
        file_path.write_text(content)
        return str(file_path)
    
    async def search_notes(
        self,
        query: str
    ) -> List[dict]:
        """搜索笔记"""
        pass
```

## 4. Webhook规范

### 4.1 Webhook接收

**端点**: `POST /webhook/{source}`

**签名验证**:
```python
def verify_webhook_signature(
    payload: bytes,
    signature: str,
    secret: str
) -> bool:
    expected = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected)
```

### 4.2 Webhook发送

**重试机制**:
- 最大重试次数: 5
- 重试间隔: 指数退避 (1s, 2s, 4s, 8s, 16s)
- 超时时间: 10秒

**事件类型**:
| 事件 | 描述 |
|------|------|
| order.created | 新订单创建 |
| order.updated | 订单状态更新 |
| message.received | 收到新消息 |
| content.published | 内容发布完成 |
| task.completed | 任务完成 |
