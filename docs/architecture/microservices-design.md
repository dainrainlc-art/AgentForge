# AgentForge 微服务架构设计文档

> **版本**: v1.0  
> **日期**: 2026-03-31  
> **状态**: 设计阶段

---

## 1. 现状分析

### 1.1 单体架构现状

当前 AgentForge 采用单体架构，所有功能模块集中在一个代码库中：

```
AgentForge (Monolith)
├── API Layer (FastAPI)
├── Business Logic
│   ├── Fiverr Management
│   ├── Social Media
│   ├── Knowledge Management
│   └── Workflow Engine
├── AI Layer
│   ├── GLM-5 Integration
│   ├── Prompt Management
│   └── Memory System
└── Data Layer
    ├── PostgreSQL
    ├── Redis
    └── Qdrant
```

**优点**:
- 开发简单，部署方便
- 代码共享容易
- 事务管理简单

**缺点**:
- 代码耦合度高
- 扩展性受限
- 技术栈绑定
- 团队并行开发困难

### 1.2 拆分动机

| 问题 | 影响 | 微服务解决方案 |
|------|------|----------------|
| 代码耦合 | 修改影响范围广 | 服务独立部署 |
| 扩展困难 | 只能整体扩容 | 按需独立扩容 |
| 技术栈限制 | 难以引入新技术 | 服务技术异构 |
| 团队效率 | 代码冲突频繁 | 团队自治 |

---

## 2. 微服务架构设计

### 2.1 服务拆分策略

采用 **领域驱动设计 (DDD)** 进行服务拆分：

```
┌─────────────────────────────────────────────────────────────┐
│                        API Gateway                           │
│              (Kong / Traefik / Nginx Ingress)               │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  User Service │    │ Order Service │    │  AI Service  │
│  用户服务      │    │  订单服务      │    │  AI 服务     │
└──────────────┘    └──────────────┘    └──────────────┘
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ Social Service│    │Knowledge Svc │    │Workflow Svc  │
│ 社交服务       │    │ 知识服务       │    │ 工作流服务    │
└──────────────┘    └──────────────┘    └──────────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     Message Queue                            │
│              (Apache Kafka / RabbitMQ / NATS)               │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 服务清单

| 服务名 | 职责 | 技术栈 | 数据库 |
|--------|------|--------|--------|
| **user-service** | 用户管理、认证授权 | FastAPI + JWT | PostgreSQL |
| **order-service** | Fiverr 订单管理 | FastAPI | PostgreSQL |
| **ai-service** | AI 模型调用、提示词管理 | FastAPI + OpenAI | Redis |
| **social-service** | 社交媒体管理 | FastAPI | PostgreSQL |
| **knowledge-service** | 知识库、文档管理 | FastAPI | PostgreSQL + Qdrant |
| **workflow-service** | 工作流引擎 | FastAPI + Temporal | PostgreSQL |
| **notification-service** | 通知服务 | FastAPI | Redis |
| **analytics-service** | 数据分析 | FastAPI + ClickHouse | ClickHouse |

### 2.3 服务间通信

#### 同步通信 (REST/gRPC)
- 用户请求处理
- 实时数据查询
- 服务间直接调用

#### 异步通信 (Message Queue)
- 订单状态变更
- 通知发送
- 数据分析
- 工作流执行

```python
# 异步消息示例
async def publish_order_created(order_id: str):
    await message_bus.publish("order.created", {
        "order_id": order_id,
        "timestamp": datetime.now().isoformat()
    })
```

---

## 3. 技术选型

### 3.1 服务网格: Istio

**选择理由**:
- 服务发现与负载均衡
- 流量管理（金丝雀发布、A/B测试）
- 安全通信（mTLS）
- 可观测性（追踪、监控）

**架构**:
```
┌─────────────────────────────────────┐
│           Istio Ingress              │
│      (Gateway + VirtualService)      │
└─────────────────────────────────────┘
                   │
    ┌──────────────┼──────────────┐
    │              │              │
    ▼              ▼              ▼
┌──────┐     ┌──────┐     ┌──────┐
│Envoy │     │Envoy │     │Envoy │  # Sidecar Proxy
│Sidecar│    │Sidecar│    │Sidecar│
└──┬───┘     └──┬───┘     └──┬───┘
   │            │            │
┌──┴───┐     ┌──┴───┐     ┌──┴───┐
│Service│     │Service│     │Service│
│   A   │     │   B   │     │   C   │
└───────┘     └───────┘     └───────┘
```

### 3.2 API 网关: Kong

**功能**:
- 路由管理
- 认证鉴权（JWT、OAuth2）
- 速率限制
- 请求/响应转换
- 缓存

**配置示例**:
```yaml
# kong.yml
services:
  - name: user-service
    url: http://user-service:8000
    routes:
      - name: user-routes
        paths:
          - /api/users
    plugins:
      - name: rate-limiting
        config:
          minute: 100
      - name: jwt
```

### 3.3 消息队列: Apache Kafka

**使用场景**:
- 订单事件流
- 用户行为日志
- 通知队列
- 数据同步

**Topic 设计**:
```
order.created
order.updated
order.completed
user.registered
notification.send
analytics.event
```

### 3.4 服务注册与发现: Consul

**功能**:
- 服务注册
- 健康检查
- 配置中心
- 服务发现

### 3.5 分布式追踪: Jaeger

**追踪流程**:
```
User Request → API Gateway → Service A → Service B → Database
     │              │            │           │          │
     └──────────────┴────────────┴───────────┴──────────┘
                         Jaeger Trace
```

---

## 4. 数据管理

### 4.1 数据库拆分

每个服务拥有独立数据库：

| 服务 | 数据库 | 数据类型 |
|------|--------|----------|
| user-service | PostgreSQL | 用户数据 |
| order-service | PostgreSQL | 订单数据 |
| knowledge-service | PostgreSQL + Qdrant | 文档 + 向量 |
| analytics-service | ClickHouse | 时序数据 |

### 4.2 数据一致性

#### Saga 模式
处理分布式事务：

```python
# 订单创建 Saga
class OrderCreationSaga:
    async def execute(self, order_data):
        try:
            # Step 1: 创建订单
            order = await order_service.create(order_data)
            
            # Step 2: 扣减库存
            await inventory_service.reserve(order.items)
            
            # Step 3: 发送通知
            await notification_service.send(order.user_id, "订单创建成功")
            
        except Exception as e:
            # 补偿操作
            await self.compensate(order)
    
    async def compensate(self, order):
        # 回滚操作
        await inventory_service.release(order.items)
        await order_service.cancel(order.id)
```

#### 事件溯源
关键业务数据使用事件溯源：

```python
# 订单事件
class OrderCreatedEvent:
    order_id: str
    user_id: str
    items: List[OrderItem]
    timestamp: datetime

class OrderPaidEvent:
    order_id: str
    payment_id: str
    amount: Decimal
    timestamp: datetime
```

---

## 5. 部署架构

### 5.1 Kubernetes 部署

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: user-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: user-service
  template:
    metadata:
      labels:
        app: user-service
    spec:
      containers:
        - name: user-service
          image: agentforge/user-service:v1.0
          ports:
            - containerPort: 8000
          env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: db-secret
                  key: url
```

### 5.2 CI/CD 流程

```
Code Commit → Build → Test → Security Scan → Deploy to Staging
                                                      │
                                                      ▼
                                              Integration Test
                                                      │
                                                      ▼
                                              Deploy to Production
                                                      │
                                              ┌──────┴──────┐
                                              ▼             ▼
                                         Canary (10%)   Full Rollout
```

---

## 6. 迁移方案

### 6.1 迁移策略: Strangler Fig

逐步替换单体应用：

```
Phase 1: 提取用户服务
┌─────────────────────────────────────┐
│         API Gateway (Kong)          │
└─────────────────────────────────────┘
         │                 │
         ▼                 ▼
┌──────────────┐   ┌──────────────┐
│ user-service │   │  Monolith    │
│   (New)      │   │  (Others)    │
└──────────────┘   └──────────────┘

Phase 2: 提取订单服务
Phase 3: 提取 AI 服务
Phase 4: 提取其他服务
Phase 5: 下线单体应用
```

### 6.2 迁移步骤

| 阶段 | 任务 | 时长 | 风险 |
|------|------|------|------|
| 1 | 搭建基础设施 | 1周 | 低 |
| 2 | 提取用户服务 | 2周 | 中 |
| 3 | 提取订单服务 | 2周 | 中 |
| 4 | 提取 AI 服务 | 2周 | 中 |
| 5 | 提取其他服务 | 4周 | 高 |
| 6 | 下线单体应用 | 1周 | 高 |

**总计**: 12 周

---

## 7. 性能与扩展

### 7.1 扩展策略

| 服务 | 扩展方式 | 触发条件 |
|------|----------|----------|
| user-service | 水平扩展 | CPU > 70% |
| order-service | 水平扩展 | 订单量 > 1000/min |
| ai-service | 水平扩展 | 请求延迟 > 500ms |
| knowledge-service | 垂直扩展 | 内存 > 80% |

### 7.2 性能指标

| 指标 | 目标 | 监控工具 |
|------|------|----------|
| API 响应时间 | < 100ms | Prometheus |
| 服务间调用 | < 50ms | Jaeger |
| 数据库查询 | < 20ms | PostgreSQL Exporter |
| 消息延迟 | < 100ms | Kafka Exporter |

---

## 8. 安全设计

### 8.1 服务间安全

- **mTLS**: Istio 自动启用双向 TLS
- **服务认证**: JWT Token
- **网络策略**: Kubernetes NetworkPolicy

### 8.2 API 安全

- **认证**: OAuth2 + JWT
- **授权**: RBAC
- **限流**: 基于令牌桶算法
- **审计**: 所有 API 调用日志

---

## 9. 监控与可观测性

### 9.1 监控体系

```
┌─────────────────────────────────────────────────────────┐
│                    Prometheus                            │
│  (Metrics Collection)                                    │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                     Grafana                              │
│  (Visualization & Alerting)                              │
└─────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│   Jaeger     │   │    Loki      │   │  Alertmanager│
│   (Tracing)  │   │   (Logging)  │   │  (Alerting)  │
└──────────────┘   └──────────────┘   └──────────────┘
```

### 9.2 关键指标

- **RED 指标**: Rate, Errors, Duration
- **USE 指标**: Utilization, Saturation, Errors
- **业务指标**: 订单量、用户数、收入

---

## 10. 成本估算

### 10.1 基础设施成本（月度）

| 组件 | 配置 | 数量 | 成本 |
|------|------|------|------|
| Kubernetes 集群 | 8核16G | 5节点 | ¥3,000 |
| PostgreSQL | 4核8G | 3实例 | ¥1,500 |
| Redis | 2核4G | 2实例 | ¥500 |
| Kafka | 4核8G | 3节点 | ¥1,500 |
| Load Balancer | - | 2个 | ¥200 |
| **总计** | | | **¥6,700/月** |

### 10.2 人力成本

| 角色 | 人数 | 时长 | 成本 |
|------|------|------|------|
| 架构师 | 1 | 12周 | ¥60,000 |
| 后端开发 | 3 | 12周 | ¥180,000 |
| DevOps | 1 | 12周 | ¥40,000 |
| 测试 | 1 | 6周 | ¥20,000 |
| **总计** | | | **¥300,000** |

---

## 11. 风险评估

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| 数据不一致 | 中 | 高 | Saga 模式、事件溯源 |
| 服务故障 | 中 | 高 | 熔断、降级、重试 |
| 性能下降 | 低 | 中 | 缓存、异步、优化 |
| 团队学习成本 | 高 | 中 | 培训、文档、POC |

---

## 12. 总结

### 微服务优势
- ✅ 独立部署、扩展
- ✅ 技术栈灵活
- ✅ 团队自治
- ✅ 故障隔离

### 微服务挑战
- ⚠️ 分布式复杂性
- ⚠️ 数据一致性
- ⚠️ 运维成本增加
- ⚠️ 团队技能要求

### 建议
1. **当前阶段**: 单体架构已满足需求
2. **未来考虑**: 用户量 > 10万时考虑迁移
3. **渐进式**: 采用 Strangler Fig 模式逐步迁移

---

**文档版本**: v1.0  
**最后更新**: 2026-03-31  
**作者**: AI Assistant  
**状态**: 设计完成，待评审
