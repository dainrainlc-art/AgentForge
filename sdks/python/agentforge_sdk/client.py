"""
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
