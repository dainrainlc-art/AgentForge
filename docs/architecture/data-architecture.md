# AgentForge 数据架构设计

## 1. 数据库Schema设计

### 1.1 订单数据模型

```sql
-- 订单表
CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    fiverr_order_id VARCHAR(100) UNIQUE NOT NULL,
    customer_id UUID REFERENCES customers(id),
    
    -- 基本信息
    title VARCHAR(500) NOT NULL,
    description TEXT,
    service_type VARCHAR(100),
    
    -- 财务信息
    budget DECIMAL(10, 2),
    currency VARCHAR(10) DEFAULT 'USD',
    actual_price DECIMAL(10, 2),
    
    -- 时间信息
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deadline TIMESTAMP WITH TIME ZONE,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- 状态
    status VARCHAR(50) DEFAULT 'pending',
    priority VARCHAR(20) DEFAULT 'normal',
    
    -- 交付物
    deliverables JSONB DEFAULT '[]',
    delivery_notes TEXT,
    
    -- 元数据
    tags VARCHAR(100)[],
    metadata JSONB DEFAULT '{}',
    
    -- 索引优化
    CONSTRAINT valid_status CHECK (status IN (
        'pending', 'in_progress', 'delivered', 
        'completed', 'cancelled', 'revision'
    ))
);

CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_created ON orders(created_at DESC);
CREATE INDEX idx_orders_deadline ON orders(deadline);
CREATE INDEX idx_orders_customer ON orders(customer_id);
```

### 1.2 客户数据模型

```sql
-- 客户表
CREATE TABLE customers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    fiverr_customer_id VARCHAR(100) UNIQUE,
    
    -- 基本信息
    name VARCHAR(255),
    email VARCHAR(255),
    company VARCHAR(255),
    country VARCHAR(100),
    timezone VARCHAR(50),
    
    -- 统计信息
    total_orders INTEGER DEFAULT 0,
    total_spent DECIMAL(12, 2) DEFAULT 0,
    avg_rating DECIMAL(3, 2),
    
    -- 沟通偏好
    preferred_language VARCHAR(10) DEFAULT 'en',
    communication_style VARCHAR(50),
    
    -- 状态
    status VARCHAR(50) DEFAULT 'active',
    vip_level INTEGER DEFAULT 0,
    
    -- 时间戳
    first_contact TIMESTAMP WITH TIME ZONE,
    last_contact TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- 备注
    notes TEXT,
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_customers_email ON customers(email);
CREATE INDEX idx_customers_status ON customers(status);
CREATE INDEX idx_customers_vip ON customers(vip_level DESC);
```

### 1.3 内容数据模型

```sql
-- 内容表
CREATE TABLE contents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- 基本信息
    title VARCHAR(500) NOT NULL,
    content_type VARCHAR(50) NOT NULL,
    platform VARCHAR(50),
    
    -- 内容
    raw_content TEXT,
    processed_content TEXT,
    formatted_content JSONB,
    
    -- 生成信息
    prompt_used TEXT,
    model_used VARCHAR(50),
    generation_params JSONB,
    
    -- 状态
    status VARCHAR(50) DEFAULT 'draft',
    version INTEGER DEFAULT 1,
    
    -- 发布信息
    published_at TIMESTAMP WITH TIME ZONE,
    published_url VARCHAR(1000),
    post_id VARCHAR(255),
    
    -- 效果数据
    views INTEGER DEFAULT 0,
    likes INTEGER DEFAULT 0,
    comments INTEGER DEFAULT 0,
    shares INTEGER DEFAULT 0,
    
    -- 时间戳
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- 元数据
    tags VARCHAR(100)[],
    metadata JSONB DEFAULT '{}',
    
    CONSTRAINT valid_content_status CHECK (status IN (
        'draft', 'pending_review', 'approved', 
        'published', 'archived', 'rejected'
    ))
);

CREATE INDEX idx_contents_status ON contents(status);
CREATE INDEX idx_contents_platform ON contents(platform);
CREATE INDEX idx_contents_created ON contents(created_at DESC);
```

### 1.4 日志与审计数据模型

```sql
-- 操作日志表
CREATE TABLE activity_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- 操作信息
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id UUID,
    
    -- 操作者
    actor_type VARCHAR(50),
    actor_id VARCHAR(100),
    
    -- 变更内容
    old_values JSONB,
    new_values JSONB,
    
    -- 上下文
    ip_address INET,
    user_agent TEXT,
    request_id UUID,
    
    -- 时间戳
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- 元数据
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_logs_entity ON activity_logs(entity_type, entity_id);
CREATE INDEX idx_logs_action ON activity_logs(action);
CREATE INDEX idx_logs_created ON activity_logs(created_at DESC);

-- LLM调用日志表
CREATE TABLE llm_call_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- 调用信息
    model VARCHAR(50) NOT NULL,
    task_type VARCHAR(100),
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    total_tokens INTEGER,
    
    -- 性能
    response_time_ms INTEGER,
    status VARCHAR(20),
    
    -- 错误信息
    error_message TEXT,
    error_code VARCHAR(50),
    
    -- 成本
    estimated_cost DECIMAL(10, 6),
    
    -- 时间戳
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- 元数据
    request_id UUID,
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_llm_logs_model ON llm_call_logs(model);
CREATE INDEX idx_llm_logs_created ON llm_call_logs(created_at DESC);
CREATE INDEX idx_llm_logs_status ON llm_call_logs(status);
```

## 2. 数据流架构

### 2.1 订单数据流

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            订单数据流                                        │
└─────────────────────────────────────────────────────────────────────────────┘

Fiverr平台
    │
    │ 1. 订单事件
    ▼
┌──────────────┐
│ N8N Webhook  │ ◄── 接收订单事件
└──────┬───────┘
       │
       │ 2. 事件处理
       ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ 事件分类器   │ ──► │ 数据提取器   │ ──► │ 数据验证器   │
└──────────────┘     └──────────────┘     └──────────────┘
       │
       │ 3. 数据存储
       ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ PostgreSQL   │ ──► │   Redis      │ ──► │   Qdrant     │
│  主存储      │     │  缓存/索引   │     │  向量索引    │
└──────────────┘     └──────────────┘     └──────────────┘
       │
       │ 4. 后续处理
       ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ GLM-5分析    │ ──► │ 通知推送     │ ──► │ 知识库更新   │
│ 报价建议     │     │ 桌面/Telegram│     │ Obsidian     │
└──────────────┘     └──────────────┘     └──────────────┘
```

### 2.2 内容数据流

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            内容数据流                                        │
└─────────────────────────────────────────────────────────────────────────────┘

用户请求
    │
    │ 1. 内容生成请求
    ▼
┌──────────────┐
│ AgentForge   │ ◄── 意图识别、任务路由
│    Core      │
└──────┬───────┘
       │
       │ 2. 内容生成
       ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Prompt模板   │ ──► │   GLM-5      │ ──► │ 响应解析     │
│   选择       │     │   生成       │     │   验证       │
└──────────────┘     └──────────────┘     └──────────────┘
       │
       │ 3. 审核流程
       ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ 审核队列     │ ──► │ 人工审核     │ ──► │ 审核结果     │
│ (Redis)      │     │ (UI)         │     │ 记录         │
└──────────────┘     └──────────────┘     └──────────────┘
       │
       │ 4. 发布流程
       ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ N8N工作流    │ ──► │ 平台API      │ ──► │ 效果追踪     │
│ 执行         │     │ 发布         │     │ 更新         │
└──────────────┘     └──────────────┘     └──────────────┘
```

### 2.3 知识数据流

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            知识数据流                                        │
└─────────────────────────────────────────────────────────────────────────────┘

Obsidian本地
    │
    │ 1. 文件变更
    ▼
┌──────────────┐
│ 文件监控器   │ ◄── 监控vault变更
└──────┬───────┘
       │
       │ 2. 变更处理
       ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ 变更分类     │ ──► │ 格式转换     │ ──► │ 冲突检测     │
│ 新增/修改    │     │ MD→Notion    │     │ 版本比对     │
└──────────────┘     └──────────────┘     └──────────────┘
       │
       │ 3. 同步执行
       ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ N8N同步      │ ──► │ Notion API   │ ──► │ 同步记录     │
│ 工作流       │     │ 更新         │     │ PostgreSQL   │
└──────────────┘     └──────────────┘     └──────────────┘
       │
       │ 4. 索引更新
       ▼
┌──────────────┐     ┌──────────────┐
│ 向量化       │ ──► │ Qdrant索引   │
│ Embedding    │     │ 更新         │
└──────────────┘     └──────────────┘
```

## 3. 缓存策略设计

### 3.1 缓存层次

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            缓存层次架构                                      │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│  L1: 应用内存缓存 (进程内)                                                   │
│  • 热点配置数据                                                              │
│  • 频繁访问的模板                                                            │
│  • TTL: 5分钟                                                               │
└─────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  L2: Redis缓存 (分布式)                                                      │
│  • 会话数据 (TTL: 24小时)                                                   │
│  • API响应缓存 (TTL: 1小时)                                                 │
│  • LLM调用缓存 (TTL: 7天)                                                   │
│  • 限流计数 (滑动窗口)                                                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  L3: PostgreSQL (持久化)                                                     │
│  • 业务数据                                                                  │
│  • 审计日志                                                                  │
│  • 配置数据                                                                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 缓存策略

**会话缓存**:
```python
SESSION_CACHE = {
    "prefix": "session:",
    "ttl": 86400,  # 24小时
    "structure": {
        "session_id": "uuid",
        "user_id": "string",
        "context": "json",
        "created_at": "timestamp",
        "last_activity": "timestamp"
    }
}
```

**API响应缓存**:
```python
API_CACHE = {
    "prefix": "api:",
    "ttl": 3600,  # 1小时
    "rules": {
        "GET /api/v1/orders": {
            "key_pattern": "orders:{user_id}:{status}:{page}",
            "ttl": 300,  # 5分钟
            "invalidate_on": ["order_create", "order_update"]
        },
        "GET /api/v1/customers": {
            "key_pattern": "customers:{user_id}:{page}",
            "ttl": 600,  # 10分钟
            "invalidate_on": ["customer_create", "customer_update"]
        }
    }
}
```

**LLM调用缓存**:
```python
LLM_CACHE = {
    "prefix": "llm:",
    "ttl": 604800,  # 7天
    "key_generation": "hash(prompt + model + params)",
    "benefit": "节省API配额，提高响应速度"
}
```

### 3.3 缓存失效机制

**主动失效**:
- 数据更新时主动删除相关缓存
- 使用发布/订阅模式通知所有节点

**被动失效**:
- TTL到期自动删除
- LRU淘汰策略

**失效策略**:
```python
CACHE_INVALIDATION = {
    "order_updated": [
        "orders:*:{order_id}",
        "customer_orders:{customer_id}:*"
    ],
    "content_published": [
        "contents:{content_id}",
        "contents:list:*"
    ],
    "knowledge_synced": [
        "knowledge:search:*",
        "knowledge:document:{doc_id}"
    ]
}
```

## 4. 同步与冲突处理

### 4.1 同步策略

**双向同步**:
```
Obsidian ◄────────────────────► Notion
   │                                │
   │    N8N同步工作流               │
   │    (每6小时 + 变更触发)        │
   │                                │
   ▼                                ▼
本地变更 ───────────────────► 云端更新
云端变更 ◄─────────────────── 本地更新
```

### 4.2 冲突检测

**冲突类型**:
| 类型 | 描述 | 解决策略 |
|------|------|----------|
| 内容冲突 | 同一文档两端都有修改 | 人工合并 |
| 删除冲突 | 一端删除，一端修改 | 保留修改版本 |
| 结构冲突 | 格式不兼容 | 转换后保留 |

**冲突检测算法**:
```python
def detect_conflict(
    local_version: Document,
    remote_version: Document,
    base_version: Document
) -> ConflictResult:
    """检测文档冲突"""
    local_changed = local_version.hash != base_version.hash
    remote_changed = remote_version.hash != base_version.hash
    
    if local_changed and remote_changed:
        if local_version.hash == remote_version.hash:
            return ConflictResult.NO_CONFLICT
        else:
            return ConflictResult.CONTENT_CONFLICT
    return ConflictResult.NO_CONFLICT
```

### 4.3 冲突解决

**自动解决**:
- 时间戳优先：最后修改者胜出
- 来源优先：本地优先或云端优先

**人工解决**:
- 生成合并建议
- 展示差异对比
- 用户选择保留版本
