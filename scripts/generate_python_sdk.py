#!/usr/bin/env python3
"""
Python SDK Generator for AgentForge API
基于 OpenAPI schema 自动生成 Python SDK
"""
import json
import os
from pathlib import Path


class PythonSDKGenerator:
    """Python SDK 生成器"""
    
    def __init__(self, openapi_path: str, output_dir: str):
        self.openapi_path = openapi_path
        self.output_dir = output_dir
        self.spec = {}
        
    def load_spec(self):
        """加载 OpenAPI 规范"""
        with open(self.openapi_path, 'r', encoding='utf-8') as f:
            self.spec = json.load(f)
    
    def generate_sdk(self):
        """生成 SDK"""
        self.load_spec()
        
        # 创建输出目录
        sdk_dir = Path(self.output_dir)
        sdk_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成主客户端文件
        self._generate_client(sdk_dir)
        
        # 生成 models
        self._generate_models(sdk_dir)
        
        # 生成 setup.py
        self._generate_setup_py(sdk_dir)
        
        # 生成 README
        self._generate_readme(sdk_dir)
        
        print(f"✅ Python SDK generated at {self.output_dir}")
    
    def _generate_client(self, sdk_dir: Path):
        """生成 API 客户端"""
        client_code = '''"""
AgentForge Python SDK
Auto-generated Python client for AgentForge API
"""
import httpx
from typing import Optional, Dict, Any, List
from .models import *


class AgentForgeClient:
    """AgentForge API 客户端"""
    
    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        api_key: Optional[str] = None,
        timeout: float = 30.0
    ):
        """初始化客户端
        
        Args:
            base_url: API 基础 URL
            api_key: API 密钥（可选）
            timeout: 请求超时时间（秒）
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(self.timeout)
        )
        if self.api_key:
            self._client.headers.update({"Authorization": f"Bearer {self.api_key}"})
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self._client:
            await self._client.aclose()
    
    async def request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> httpx.Response:
        """发送 HTTP 请求
        
        Args:
            method: HTTP 方法
            endpoint: API 端点
            **kwargs: 请求参数
            
        Returns:
            httpx.Response: HTTP 响应
            
        Raises:
            httpx.HTTPError: 请求失败时抛出
        """
        if not self._client:
            async with httpx.AsyncClient() as client:
                response = await client.request(method, f"{self.base_url}{endpoint}", **kwargs)
                return response
        
        response = await self._client.request(method, endpoint, **kwargs)
        return response
    
    # ========== 认证相关 ==========
    
    async def login(self, username: str, password: str) -> Dict[str, Any]:
        """用户登录
        
        Args:
            username: 用户名
            password: 密码
            
        Returns:
            包含 access_token 和 refresh_token 的字典
        """
        response = await self.request(
            "POST",
            "/api/auth/login",
            json={"username": username, "password": password}
        )
        response.raise_for_status()
        return response.json()
    
    async def register(self, username: str, email: str, password: str) -> Dict[str, Any]:
        """用户注册
        
        Args:
            username: 用户名
            email: 邮箱
            password: 密码
            
        Returns:
            注册结果
        """
        response = await self.request(
            "POST",
            "/api/auth/register",
            json={"username": username, "email": email, "password": password}
        )
        response.raise_for_status()
        return response.json()
    
    # ========== 健康检查 ==========
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查
        
        Returns:
            服务健康状态
        """
        response = await self.request("GET", "/api/health")
        response.raise_for_status()
        return response.json()
    
    # ========== Fiverr 订单管理 ==========
    
    async def get_orders(
        self,
        status: Optional[str] = None,
        limit: int = 10,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """获取订单列表
        
        Args:
            status: 订单状态过滤
            limit: 返回数量限制
            offset: 偏移量
            
        Returns:
            订单列表
        """
        params = {"limit": limit, "offset": offset}
        if status:
            params["status"] = status
        
        response = await self.request("GET", "/api/orders", params=params)
        response.raise_for_status()
        return response.json()
    
    async def get_order(self, order_id: str) -> Dict[str, Any]:
        """获取订单详情
        
        Args:
            order_id: 订单 ID
            
        Returns:
            订单详情
        """
        response = await self.request("GET", f"/api/orders/{order_id}")
        response.raise_for_status()
        return response.json()
    
    async def update_order_status(
        self,
        order_id: str,
        status: str,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """更新订单状态
        
        Args:
            order_id: 订单 ID
            status: 新状态
            notes: 备注（可选）
            
        Returns:
            更新结果
        """
        response = await self.request(
            "PATCH",
            f"/api/orders/{order_id}/status",
            json={"status": status, "notes": notes}
        )
        response.raise_for_status()
        return response.json()
    
    # ========== 知识管理 ==========
    
    async def sync_knowledge(
        self,
        source: str,
        target: str
    ) -> Dict[str, Any]:
        """同步知识
        
        Args:
            source: 源路径
            target: 目标路径
            
        Returns:
            同步结果
        """
        response = await self.request(
            "POST",
            "/api/knowledge/sync",
            json={"source": source, "target": target}
        )
        response.raise_for_status()
        return response.json()
    
    async def search_knowledge(
        self,
        query: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """搜索知识
        
        Args:
            query: 搜索关键词
            limit: 返回数量限制
            
        Returns:
            搜索结果列表
        """
        response = await self.request(
            "GET",
            "/api/knowledge/search",
            params={"query": query, "limit": limit}
        )
        response.raise_for_status()
        return response.json()
    
    # ========== Chat ==========
    
    async def chat(
        self,
        message: str,
        agent: str = "default"
    ) -> Dict[str, Any]:
        """发送聊天消息
        
        Args:
            message: 消息内容
            agent: Agent ID
            
        Returns:
            AI 回复
        """
        response = await self.request(
            "POST",
            "/api/chat",
            json={"message": message, "agent": agent}
        )
        response.raise_for_status()
        return response.json()
    
    # ========== 监控 ==========
    
    async def get_metrics(self) -> Dict[str, Any]:
        """获取系统指标
        
        Returns:
            系统指标数据
        """
        response = await self.request("GET", "/api/metrics")
        response.raise_for_status()
        return response.json()
    
    async def get_performance(self) -> Dict[str, Any]:
        """获取性能数据
        
        Returns:
            性能数据
        """
        response = await self.request("GET", "/api/performance")
        response.raise_for_status()
        return response.json()


# 同步客户端（用于向后兼容）
class SyncAgentForgeClient:
    """同步版本的 AgentForge API 客户端"""
    
    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        api_key: Optional[str] = None,
        timeout: float = 30.0
    ):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        self._client: Optional[httpx.Client] = None
    
    def __enter__(self):
        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=httpx.Timeout(self.timeout)
        )
        if self.api_key:
            self._client.headers.update({"Authorization": f"Bearer {self.api_key}"})
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            self._client.close()
    
    def request(self, method: str, endpoint: str, **kwargs) -> httpx.Response:
        if not self._client:
            with httpx.Client() as client:
                return client.request(method, f"{self.base_url}{endpoint}", **kwargs)
        return self._client.request(method, endpoint, **kwargs)
    
    def login(self, username: str, password: str) -> Dict[str, Any]:
        response = self.request(
            "POST",
            "/api/auth/login",
            json={"username": username, "password": password}
        )
        response.raise_for_status()
        return response.json()
    
    def health_check(self) -> Dict[str, Any]:
        response = self.request("GET", "/api/health")
        response.raise_for_status()
        return response.json()


__all__ = [
    "AgentForgeClient",
    "SyncAgentForgeClient",
]
'''
        
        # 写入文件
        (sdk_dir / "client.py").write_text(client_code, encoding='utf-8')
        
        # 写入 __init__.py
        init_code = '''"""
AgentForge Python SDK

Usage:
    from agentforge_sdk import AgentForgeClient
    
    async with AgentForgeClient(base_url="http://localhost:8000") as client:
        # 健康检查
        health = await client.health_check()
        
        # 登录
        tokens = await client.login("username", "password")
        
        # 获取订单
        orders = await client.get_orders()
        
        # 聊天
        response = await client.chat("你好")
"""
from .client import AgentForgeClient, SyncAgentForgeClient
from .models import *

__version__ = "1.0.0"
__author__ = "AgentForge Team"

__all__ = [
    "AgentForgeClient",
    "SyncAgentForgeClient",
    "__version__",
]
'''
        (sdk_dir / "__init__.py").write_text(init_code, encoding='utf-8')
    
    def _generate_models(self, sdk_dir: Path):
        """生成数据模型"""
        models_code = '''"""
数据模型定义
"""
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime


@dataclass
class Order:
    """订单模型"""
    order_id: str
    title: str
    description: str
    status: str
    price: float
    created_at: datetime
    updated_at: Optional[datetime] = None


@dataclass
class User:
    """用户模型"""
    user_id: str
    username: str
    email: str
    created_at: datetime


@dataclass
class Knowledge:
    """知识模型"""
    id: str
    title: str
    content: str
    source: str
    created_at: datetime


@dataclass
class ChatMessage:
    """聊天消息模型"""
    role: str
    content: str
    timestamp: Optional[datetime] = None


@dataclass
class HealthStatus:
    """健康状态模型"""
    status: str
    version: str
    timestamp: datetime


__all__ = [
    "Order",
    "User",
    "Knowledge",
    "ChatMessage",
    "HealthStatus",
]
'''
        (sdk_dir / "models.py").write_text(models_code, encoding='utf-8')
    
    def _generate_setup_py(self, sdk_dir: Path):
        """生成 setup.py"""
        setup_code = '''"""
AgentForge Python SDK
"""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="agentforge-sdk",
    version="1.0.0",
    author="AgentForge Team",
    author_email="contact@agentforge.com",
    description="Python SDK for AgentForge API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/agentforge/agentforge-python-sdk",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=[
        "httpx>=0.25.0",
        "pydantic>=2.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "mypy>=1.0.0",
        ],
    },
)
'''
        (sdk_dir / "setup.py").write_text(setup_code, encoding='utf-8')
    
    def _generate_readme(self, sdk_dir: Path):
        """生成 README"""
        readme_code = '''# AgentForge Python SDK

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
'''
        (sdk_dir / "README.md").write_text(readme_code, encoding='utf-8')


if __name__ == "__main__":
    generator = PythonSDKGenerator(
        openapi_path="docs/api/openapi.json",
        output_dir="sdks/python/agentforge_sdk"
    )
    generator.generate_sdk()
