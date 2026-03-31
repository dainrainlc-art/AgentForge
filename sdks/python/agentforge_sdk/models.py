"""
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
