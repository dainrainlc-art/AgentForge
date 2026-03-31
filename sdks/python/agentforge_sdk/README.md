# AgentForge Python SDK

Python SDK for AgentForge API.

## 安装

```bash
pip install agentforge-sdk
```

或者从源码安装：

```bash
cd sdks/python
pip install -e .
```

## 快速开始

### 异步客户端

```python
import asyncio
from agentforge_sdk import AgentForgeClient

async def main():
    async with AgentForgeClient(
        base_url="http://localhost:8000",
        api_key="your-api-key"
    ) as client:
        # 健康检查
        health = await client.health_check()
        print(f"Service status: {health['status']}")
        
        # 登录
        tokens = await client.login("username", "password")
        print(f"Access token: {tokens['access_token']}")
        
        # 获取订单
        orders = await client.get_orders(status="active")
        print(f"Found {len(orders)} active orders")
        
        # 聊天
        response = await client.chat("你好，请帮我创建一个 Fiverr 订单报价")
        print(f"AI response: {response['message']}")

asyncio.run(main())
```

### 同步客户端

```python
from agentforge_sdk import SyncAgentForgeClient

with SyncAgentForgeClient(base_url="http://localhost:8000") as client:
    # 健康检查
    health = client.health_check()
    print(f"Service status: {health['status']}")
    
    # 登录
    tokens = client.login("username", "password")
    print(f"Access token: {tokens['access_token']}")
```

## API 参考

### 认证相关

- `login(username, password)` - 用户登录
- `register(username, email, password)` - 用户注册

### 健康检查

- `health_check()` - 服务健康检查

### Fiverr 订单管理

- `get_orders(status, limit, offset)` - 获取订单列表
- `get_order(order_id)` - 获取订单详情
- `update_order_status(order_id, status, notes)` - 更新订单状态

### 知识管理

- `sync_knowledge(source, target)` - 同步知识
- `search_knowledge(query, limit)` - 搜索知识

### Chat

- `chat(message, agent)` - 发送聊天消息

### 监控

- `get_metrics()` - 获取系统指标
- `get_performance()` - 获取性能数据

## 错误处理

```python
from agentforge_sdk import AgentForgeClient
import httpx

async with AgentForgeClient() as client:
    try:
        response = await client.login("username", "password")
    except httpx.HTTPError as e:
        print(f"HTTP error: {e}")
    except Exception as e:
        print(f"Error: {e}")
```

## 开发

运行测试：

```bash
pytest tests/
```

运行类型检查：

```bash
mypy agentforge_sdk/
```

## 许可证

MIT License
