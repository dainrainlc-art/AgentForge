"""
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
