# AgentForge 集成测试快速参考

## 文件结构

```
tests/integration/
├── conftest.py                    # 测试配置和夹具
├── README.md                      # 详细测试文档
├── COMPLETION_SUMMARY.md          # 完成总结
├── test_database_integration.py   # 数据库集成测试 (19 个测试)
├── test_api_integration.py        # API 集成测试 (34 个测试)
├── test_workflow_integration.py   # 工作流集成测试 (24 个测试)
└── test_e2e.py                    # 端到端测试 (8 个测试)
```

## 快速运行命令

### 1. 启动必要服务
```bash
# 启动数据库和缓存服务
docker-compose up -d postgres redis qdrant

# 等待服务启动
sleep 10

# 验证服务状态
docker-compose ps
```

### 2. 运行所有集成测试
```bash
# 运行所有测试
pytest tests/integration/ -v

# 运行并生成覆盖率报告
pytest tests/integration/ -v --cov=agentforge --cov-report=html

# 运行并生成 HTML 报告
pytest tests/integration/ -v --html=reports/report.html
```

### 3. 运行特定测试类别
```bash
# 数据库测试
pytest tests/integration/test_database_integration.py -v

# API 测试
pytest tests/integration/test_api_integration.py -v

# 工作流测试
pytest tests/integration/test_workflow_integration.py -v

# 端到端测试
pytest tests/integration/test_e2e.py -v
```

### 4. 运行特定测试类
```bash
# PostgreSQL 测试
pytest tests/integration/test_database_integration.py::TestPostgreSQLIntegration -v

# Redis 测试
pytest tests/integration/test_database_integration.py::TestRedisIntegration -v

# Qdrant 测试
pytest tests/integration/test_database_integration.py::TestQdrantIntegration -v

# 健康检查 API 测试
pytest tests/integration/test_api_integration.py::TestHealthAPI -v

# 订单 API 测试
pytest tests/integration/test_api_integration.py::TestOrdersAPI -v

# 工作流管理测试
pytest tests/integration/test_workflow_integration.py::TestWorkflowManagement -v

# Fiverr 订单端到端测试
pytest tests/integration/test_e2e.py::TestFiverrOrderE2E -v
```

### 5. 运行单个测试
```bash
# 运行单个测试方法
pytest tests/integration/test_database_integration.py::TestPostgreSQLIntegration::test_database_connection -v

# 运行并显示输出
pytest tests/integration/test_api_integration.py::TestHealthAPI::test_health_check -v -s
```

### 6. 调试测试
```bash
# 显示详细日志
pytest tests/integration/ -v --log-cli-level=INFO

# 失败时进入调试器
pytest tests/integration/ --pdb

# 不捕获输出
pytest tests/integration/ -v -s
```

## 测试夹具快速参考

### 数据库夹具
```python
# 在测试中使用
async def test_example(db_session, redis_client, qdrant_client):
    # db_session: PostgreSQL 异步会话
    # redis_client: Redis 异步客户端
    # qdrant_client: Qdrant 异步客户端
    pass
```

### API 测试夹具
```python
# 在测试中使用
async def test_api(client, auth_headers):
    # client: httpx 异步 HTTP 客户端
    # auth_headers: 模拟的认证头
    response = await client.get("/api/health")
    pass
```

### 模拟服务夹具
```python
# 在测试中使用
async def test_with_mocks(mock_external_services):
    # mock_external_services["qianfan"]: 模拟千帆 API
    # mock_external_services["n8n"]: 模拟 N8N
    # mock_external_services["fiverr"]: 模拟 Fiverr API
    pass
```

## 测试数据夹具

```python
# 在测试中使用
async def test_with_data(sample_order_data, sample_knowledge_doc, sample_user_data):
    # sample_order_data: 示例订单数据
    # sample_knowledge_doc: 示例知识文档
    # sample_user_data: 示例用户数据
    pass
```

## 常见测试场景

### 1. 数据库 CRUD 测试
```python
@pytest.mark.asyncio
async def test_crud(db_session):
    # Create
    await db_session.execute(text("INSERT ..."))
    await db_session.commit()
    
    # Read
    result = await db_session.execute(text("SELECT ..."))
    
    # Update
    await db_session.execute(text("UPDATE ..."))
    await db_session.commit()
    
    # Delete
    await db_session.execute(text("DELETE ..."))
    await db_session.commit()
```

### 2. API 测试
```python
@pytest.mark.asyncio
async def test_api(client, auth_headers):
    # GET 请求
    response = await client.get("/api/resource")
    
    # POST 请求
    response = await client.post("/api/resource", json=data)
    
    # PUT 请求
    response = await client.put(f"/api/resource/{id}", json=data)
    
    # DELETE 请求
    response = await client.delete(f"/api/resource/{id}")
```

### 3. 端到端测试
```python
@pytest.mark.asyncio
async def test_e2e(e2e_client, db_session, mock_external_services):
    # 1. 准备测试数据
    # 2. 触发业务流程
    # 3. 验证数据库状态
    # 4. 验证外部服务调用
    # 5. 清理数据
    pass
```

## 测试标记（Markers）

```bash
# 运行所有集成测试
pytest -m integration -v

# 运行所有端到端测试
pytest -m e2e -v

# 运行所有慢速测试
pytest -m slow -v

# 排除慢速测试
pytest -m "not slow" -v
```

## 故障排除

### 服务连接失败
```bash
# 检查服务状态
docker-compose ps

# 查看服务日志
docker-compose logs postgres
docker-compose logs redis
docker-compose logs qdrant

# 重启服务
docker-compose restart
```

### 端口占用
```bash
# 检查端口占用
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis
lsof -i :6333  # Qdrant
lsof -i :5678  # N8N

# 停止占用端口的服务
sudo systemctl stop postgresql  # 如果本地运行了 PostgreSQL
```

### 测试数据清理
```bash
# 重置测试数据库
docker-compose exec postgres psql -U agentforge -c "DROP DATABASE IF EXISTS agentforge_test;"
docker-compose exec postgres psql -U agentforge -c "CREATE DATABASE agentforge_test;"

# 清理 Redis
docker-compose exec redis redis-cli FLUSHALL

# 清理 Qdrant
curl -X DELETE "http://localhost:6333/collections/*"
```

## 性能优化

### 并行运行测试
```bash
# 使用 xdist 并行运行
pip install pytest-xdist
pytest tests/integration/ -v -n auto
```

### 减少测试时间
```bash
# 跳过慢速测试
pytest tests/integration/ -v -m "not slow"

# 只运行失败的测试
pytest tests/integration/ -v --lf
```

## 持续集成

### GitHub Actions 示例
```yaml
- name: Run Integration Tests
  run: |
    docker-compose up -d postgres redis qdrant
    sleep 10
    pytest tests/integration/ -v --cov=agentforge
```

## 联系和支持

- 详细文档：`tests/integration/README.md`
- 完成总结：`tests/integration/COMPLETION_SUMMARY.md`
- 测试配置：`tests/integration/conftest.py`
