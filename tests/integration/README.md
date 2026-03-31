# AgentForge 集成测试套件

本文档描述 AgentForge 项目的集成测试套件，包括测试组织结构、测试场景和运行指南。

## 测试文件组织

```
tests/
├── integration/
│   ├── conftest.py                    # 集成测试配置和夹具
│   ├── test_database_integration.py   # 数据库集成测试
│   ├── test_api_integration.py        # API 集成测试
│   ├── test_workflow_integration.py   # 工作流集成测试
│   └── test_e2e.py                    # 端到端业务流程测试
├── unit/                              # 单元测试（已有）
├── e2e/                               # 其他端到端测试
└── conftest.py                        # 全局测试配置
```

## 测试场景覆盖

### 1. 数据库集成测试 (`test_database_integration.py`)

测试 PostgreSQL、Redis 和 Qdrant 的集成和数据流转。

**测试覆盖：**

- **PostgreSQL 测试**
  - ✅ 数据库连接测试
  - ✅ 用户 CRUD 操作
  - ✅ 订单与用户关联关系
  - ✅ 知识文档和标签存储
  - ✅ 事务回滚功能
  - ✅ 并发数据库操作

- **Redis 测试**
  - ✅ Redis 连接测试
  - ✅ 缓存增删改查
  - ✅ Hash 操作
  - ✅ 列表操作（队列）
  - ✅ 速率限制功能
  - ✅ 会话管理

- **Qdrant 测试**
  - ✅ Qdrant 连接测试
  - ✅ 向量集合操作
  - ✅ 向量相似度搜索
  - ✅ 向量负载操作
  - ✅ 带过滤的搜索

- **多数据库协同**
  - ✅ PostgreSQL + Redis 协同
  - ✅ PostgreSQL + Qdrant 协同（知识库工作流）

### 2. API 集成测试 (`test_api_integration.py`)

测试 FastAPI 应用与业务引擎的集成。

**测试覆盖：**

- **健康检查 API**
  - ✅ 基础健康检查端点
  - ✅ 根端点
  - ✅ 带数据库状态的健康检查

- **认证 API**
  - ✅ 用户注册
  - ✅ 用户登录（有效凭据）
  - ✅ 用户登录（无效凭据）
  - ✅ 登录验证

- **订单管理 API**
  - ✅ 获取订单列表
  - ✅ 根据 ID 获取订单
  - ✅ 创建订单
  - ✅ 更新订单状态
  - ✅ 删除订单
  - ✅ Fiverr 集成测试

- **知识管理 API**
  - ✅ 获取知识文档列表
  - ✅ 创建知识文档
  - ✅ 搜索知识文档
  - ✅ 更新知识文档
  - ✅ 删除知识文档
  - ✅ 向量搜索

- **Chat API**
  - ✅ 发送消息
  - ✅ 带上下文的聊天
  - ✅ 使用不同 AI 模型
  - ✅ 消息验证

- **Fiverr 分析 API**
  - ✅ 获取统计数据
  - ✅ 订单分析
  - ✅ 收入报告

- **错误处理**
  - ✅ 404 错误
  - ✅ 405 错误
  - ✅ 422 验证错误
  - ✅ CORS 头

- **性能测试**
  - ✅ 响应时间测试
  - ✅ 并发请求测试

### 3. 工作流集成测试 (`test_workflow_integration.py`)

测试 N8N 工作流引擎与业务引擎的集成。

**测试覆盖：**

- **N8N 客户端基础**
  - ✅ 客户端初始化
  - ✅ 连接初始化成功/失败

- **工作流管理**
  - ✅ 获取工作流列表
  - ✅ 获取单个工作流
  - ✅ 创建工作流
  - ✅ 激活/停用工作流
  - ✅ 删除工作流

- **工作流执行**
  - ✅ 执行工作流
  - ✅ 执行工作流（无数据）
  - ✅ 获取执行详情

- **业务场景工作流**
  - ✅ Fiverr 订单监控工作流
  - ✅ 知识同步工作流
  - ✅ 社交媒体发布工作流

- **工作流与业务引擎集成**
  - ✅ 触发 Fiverr 订单处理
  - ✅ AI 模型集成
  - ✅ 错误处理

- **定时和调度**
  - ✅ 定时触发工作流
  - ✅ Webhook 触发工作流

- **数据流转**
  - ✅ 工作流数据传递
  - ✅ 链式执行

- **性能测试**
  - ✅ 并发工作流执行
  - ✅ 执行超时测试

### 4. 端到端业务流程测试 (`test_e2e.py`)

测试完整的业务流程，模拟真实用户场景。

**测试覆盖：**

- **Fiverr 订单处理**
  - ✅ 完整订单工作流
  - ✅ 订单状态变更工作流

- **知识管理**
  - ✅ 完整知识管理工作流
  - ✅ 与外部源同步

- **社交媒体**
  - ✅ 内容生成和发布

- **客户沟通**
  - ✅ 客户消息处理

- **多模块协作**
  - ✅ 跨模块协作工作流

- **完整业务周期**
  - ✅ 从订单接收到完成的完整流程

## 运行测试

### 前置条件

1. 确保测试数据库已配置：
   ```bash
   # 在 .env 文件中配置
   POSTGRES_DB=agentforge_test
   POSTGRES_USER=agentforge
   POSTGRES_PASSWORD=test_password
   ```

2. 启动必要的服务：
   ```bash
   docker-compose up -d postgres redis qdrant
   ```

### 运行所有集成测试

```bash
# 运行所有集成测试
pytest tests/integration/ -v

# 运行带覆盖率的测试
pytest tests/integration/ -v --cov=agentforge --cov-report=html

# 运行特定测试文件
pytest tests/integration/test_database_integration.py -v
pytest tests/integration/test_api_integration.py -v
pytest tests/integration/test_workflow_integration.py -v
pytest tests/integration/test_e2e.py -v
```

### 运行特定测试类

```bash
# 运行 PostgreSQL 测试
pytest tests/integration/test_database_integration.py::TestPostgreSQLIntegration -v

# 运行 API 健康测试
pytest tests/integration/test_api_integration.py::TestHealthAPI -v

# 运行工作流管理测试
pytest tests/integration/test_workflow_integration.py::TestWorkflowManagement -v

# 运行端到端订单测试
pytest tests/integration/test_e2e.py::TestFiverrOrderE2E -v
```

### 运行带标记的测试

```bash
# 运行所有集成测试标记的测试
pytest -m integration -v

# 运行所有端到端测试
pytest -m e2e -v
```

### 生成测试报告

```bash
# 生成 HTML 报告
pytest tests/integration/ -v --html=reports/test_report.html

# 生成 XML 报告（用于 CI）
pytest tests/integration/ -v --junitxml=reports/test_results.xml

# 生成覆盖率报告
pytest tests/integration/ -v --cov=agentforge --cov-report=html
```

## 测试夹具说明

### 数据库夹具

- `db_engine`: 创建数据库引擎
- `db_session`: 创建数据库会话（每个测试函数独立，自动回滚）
- `redis_client`: 创建 Redis 客户端
- `qdrant_client`: 创建 Qdrant 客户端

### API 测试夹具

- `client`: 创建测试 HTTP 客户端（使用 httpx + ASGI）
- `auth_headers`: 模拟认证头
- `mock_external_services`: 模拟外部服务（千帆、N8N、Fiverr）

### 工作流测试夹具

- `n8n_client`: 创建 N8N 客户端实例
- `mock_httpx_client`: 模拟 httpx 客户端
- `sample_workflow_definition`: 示例工作流定义
- `fiverr_order_workflow`: Fiverr 订单工作流定义

### 数据夹具

- `sample_order_data`: 示例订单数据
- `sample_knowledge_doc`: 示例知识文档
- `sample_user_data`: 示例用户数据
- `e2e_test_data`: 端到端测试数据

## 测试最佳实践

### 1. 测试隔离

- 每个测试函数使用独立的事务
- 测试完成后自动回滚所有更改
- 使用模拟对象隔离外部服务

### 2. 测试数据管理

- 使用唯一的标识符避免冲突（如 UUID）
- 测试完成后清理数据
- 使用夹具提供一致的测试数据

### 3. 异步测试

- 使用 `@pytest.mark.asyncio` 标记异步测试
- 使用 `async/await` 语法
- 正确管理事件循环

### 4. 错误处理

- 测试正常路径和错误路径
- 验证错误消息和状态码
- 测试边界条件

### 5. 性能考虑

- 设置合理的超时时间
- 测试并发场景
- 监控资源使用

## 测试覆盖率目标

| 模块 | 目标覆盖率 | 当前状态 |
|------|-----------|---------|
| 数据库层 | 80% | ✅ 已达成 |
| API 层 | 75% | ✅ 已达成 |
| 工作流层 | 70% | ✅ 已达成 |
| 业务逻辑层 | 65% | ✅ 已达成 |
| 端到端流程 | 60% | ✅ 已达成 |

## 持续集成

在 CI/CD 流水线中运行集成测试：

```yaml
# .github/workflows/ci.yml
jobs:
  integration-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: agentforge_test
          POSTGRES_USER: agentforge
          POSTGRES_PASSWORD: test_password
        ports:
          - 5432:5432
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
      qdrant:
        image: qdrant/qdrant:latest
        ports:
          - 6333:6333
    
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run integration tests
        run: pytest tests/integration/ -v --cov=agentforge
```

## 故障排除

### 常见问题

1. **数据库连接失败**
   ```bash
   # 检查服务是否运行
   docker-compose ps
   
   # 检查端口是否被占用
   lsof -i :5432
   lsof -i :6379
   lsof -i :6333
   ```

2. **测试超时**
   ```bash
   # 增加超时时间
   pytest tests/integration/ -v --timeout=60
   ```

3. **模拟对象不工作**
   - 确保 mock 的路径正确
   - 检查 patch 的作用域
   - 验证 mock 的返回值

### 调试测试

```bash
# 使用详细输出
pytest tests/integration/ -v -s

# 在失败时进入调试器
pytest tests/integration/ --pdb

# 打印日志
pytest tests/integration/ -v --log-cli-level=INFO
```

## 测试维护

### 添加新测试

1. 确定测试类型（数据库/API/工作流/端到端）
2. 在相应的测试文件中添加测试类和方法
3. 使用现有的夹具或创建新的夹具
4. 确保测试隔离和清理

### 更新现有测试

1. 保持测试的原子性
2. 更新相关的夹具
3. 验证测试仍然通过
4. 更新文档

## 参考

- [pytest 文档](https://docs.pytest.org/)
- [pytest-asyncio 文档](https://pytest-asyncio.readthedocs.io/)
- [httpx 文档](https://www.python-httpx.org/)
- [SQLAlchemy 文档](https://docs.sqlalchemy.org/)
- [Redis 文档](https://redis.io/documentation)
- [Qdrant 文档](https://qdrant.tech/documentation/)
