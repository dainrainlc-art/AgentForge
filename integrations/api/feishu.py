"""
AgentForge Feishu Integration API
飞书 API 端点
"""
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from loguru import logger

from integrations.external.feishu_client import FeishuClient, FeishuBotManager
from integrations.external.feishu_models import (
    Notification, NotificationType, Subscriber, CalendarEvent,
    Document, MessageType
)

router = APIRouter(prefix="/api/feishu", tags=["feishu"])

# 全局客户端实例
_client: Optional[FeishuClient] = None
_manager: Optional[FeishuBotManager] = None


def get_client() -> FeishuClient:
    """获取飞书客户端实例"""
    global _client
    if _client is None:
        _client = FeishuClient()
    return _client


def get_manager() -> FeishuBotManager:
    """获取飞书管理器实例"""
    global _manager
    if _manager is None:
        _manager = FeishuBotManager(get_client())
    return _manager


class NotificationSendRequest(BaseModel):
    """发送通知请求"""
    receiver_id: str
    receiver_type: str = "user"
    notification_type: NotificationType
    title: str
    content: str
    data: Optional[Dict[str, Any]] = None


class BroadcastRequest(BaseModel):
    """广播请求"""
    notification_type: NotificationType
    title: str
    content: str
    data: Optional[Dict[str, Any]] = None


class SubscribeRequest(BaseModel):
    """订阅请求"""
    user_id: str
    open_id: str
    name: str
    email: Optional[str] = None
    notification_types: List[NotificationType] = Field(default_factory=list)


class CalendarEventRequest(BaseModel):
    """创建日历事件请求"""
    summary: str
    description: str = ""
    start_time: datetime
    end_time: datetime
    timezone: str = "Asia/Shanghai"
    location: str = ""
    attendee_ids: List[str] = Field(default_factory=list)
    reminders: List[int] = Field(default_factory=lambda: [15])


@router.get("/info")
async def get_bot_info():
    """
    获取应用信息
    
    Returns:
        应用信息
    """
    try:
        client = get_client()
        success = await client.test_connection()
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to connect to Feishu API")
        
        logger.info("Successfully connected to Feishu API")
        
        return {
            "success": True,
            "message": "Connected to Feishu API"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get Feishu info: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get Feishu info: {str(e)}")


@router.post("/send-message")
async def send_message(
    chat_id: str = Query(..., description="聊天 ID"),
    text: str = Query(..., description="消息文本"),
    message_type: str = Query("text", description="消息类型")
):
    """
    发送消息
    
    Args:
        chat_id: 聊天 ID
        text: 消息文本
        message_type: 消息类型
        
    Returns:
        发送结果
    """
    try:
        client = get_client()
        
        msg_type = MessageType(message_type)
        message = await client.send_message(
            chat_id=chat_id,
            content=f'{{"text": "{text}"}}',
            message_type=msg_type
        )
        
        if not message:
            raise HTTPException(status_code=500, detail="Failed to send message")
        
        logger.info(f"Message sent to chat {chat_id}")
        
        return {
            "success": True,
            "message_id": message.message_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send message: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send message: {str(e)}")


@router.post("/send-notification")
async def send_notification(request: NotificationSendRequest):
    """
    发送通知
    
    Args:
        request: 通知请求
        
    Returns:
        发送结果
    """
    try:
        client = get_client()
        
        notification = Notification(
            id=f"notif_{datetime.now().timestamp()}",
            type=request.notification_type,
            title=request.title,
            content=request.content,
            receiver_id=request.receiver_id,
            receiver_type=request.receiver_type,
            data=request.data
        )
        
        success = await client.send_notification(notification)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to send notification")
        
        logger.info(f"Notification sent to {request.receiver_id}")
        
        return {
            "success": True,
            "notification_id": notification.id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send notification: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send notification: {str(e)}")


@router.post("/broadcast")
async def broadcast(request: BroadcastRequest):
    """
    广播通知
    
    Args:
        request: 广播请求
        
    Returns:
        广播统计
    """
    try:
        client = get_client()
        manager = get_manager()
        
        notification = Notification(
            id=f"notif_{datetime.now().timestamp()}",
            type=request.notification_type,
            title=request.title,
            content=request.content,
            receiver_id="0",
            data=request.data
        )
        
        subscribers = manager._subscribers
        stats = await client.broadcast_notification(notification, subscribers)
        
        logger.info(f"Broadcast completed: {stats}")
        
        return {
            "success": True,
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"Failed to broadcast: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to broadcast: {str(e)}")


@router.post("/subscribe")
async def subscribe(request: SubscribeRequest):
    """
    订阅通知
    
    Args:
        request: 订阅请求
        
    Returns:
        订阅结果
    """
    try:
        manager = get_manager()
        
        # 检查是否已订阅
        existing = next((s for s in manager._subscribers if s.user_id == request.user_id), None)
        
        if existing:
            existing.subscribed_types = request.notification_types or list(NotificationType)
            existing.enabled = True
            logger.info(f"Updated subscription for user {request.user_id}")
        else:
            subscriber = Subscriber(
                user_id=request.user_id,
                open_id=request.open_id,
                name=request.name,
                email=request.email,
                subscribed_types=request.notification_types or list(NotificationType)
            )
            manager._subscribers.append(subscriber)
            logger.info(f"New subscription for user {request.user_id}")
        
        return {
            "success": True,
            "message": "Successfully subscribed"
        }
        
    except Exception as e:
        logger.error(f"Failed to subscribe: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to subscribe: {str(e)}")


@router.post("/unsubscribe")
async def unsubscribe(user_id: str = Query(..., description="用户 ID")):
    """
    取消订阅
    
    Args:
        user_id: 用户 ID
        
    Returns:
        取消结果
    """
    try:
        manager = get_manager()
        
        manager._subscribers = [s for s in manager._subscribers if s.user_id != user_id]
        
        logger.info(f"Unsubscribed user {user_id}")
        
        return {
            "success": True,
            "message": "Successfully unsubscribed"
        }
        
    except Exception as e:
        logger.error(f"Failed to unsubscribe: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to unsubscribe: {str(e)}")


@router.get("/subscribers")
async def get_subscribers():
    """
    获取订阅者列表
    
    Returns:
        订阅者列表
    """
    try:
        manager = get_manager()
        
        return {
            "success": True,
            "subscribers": [s.dict() for s in manager._subscribers],
            "total": len(manager._subscribers)
        }
        
    except Exception as e:
        logger.error(f"Failed to get subscribers: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get subscribers: {str(e)}")


@router.post("/calendar/event")
async def create_calendar_event(request: CalendarEventRequest):
    """
    创建日历事件
    
    Args:
        request: 事件请求
        
    Returns:
        创建的事件
    """
    try:
        client = get_client()
        
        event = CalendarEvent(
            event_id="",
            summary=request.summary,
            description=request.description,
            start_time=request.start_time,
            end_time=request.end_time,
            timezone=request.timezone,
            location=request.location,
            organizer_id="",
            attendee_ids=request.attendee_ids,
            reminders=request.reminders
        )
        
        created_event = await client.create_calendar_event(event)
        
        if not created_event:
            raise HTTPException(status_code=500, detail="Failed to create calendar event")
        
        logger.info(f"Calendar event created: {created_event.event_id}")
        
        return {
            "success": True,
            "event": created_event.dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create calendar event: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create calendar event: {str(e)}")


@router.get("/calendar/events")
async def get_calendar_events(
    start_time: datetime = Query(..., description="开始时间"),
    end_time: datetime = Query(..., description="结束时间")
):
    """
    获取日历事件
    
    Args:
        start_time: 开始时间
        end_time: 结束时间
        
    Returns:
        事件列表
    """
    try:
        client = get_client()
        
        events = await client.get_calendar_events(start_time, end_time)
        
        return {
            "success": True,
            "events": [e.dict() for e in events],
            "total": len(events)
        }
        
    except Exception as e:
        logger.error(f"Failed to get calendar events: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get calendar events: {str(e)}")


@router.get("/document/{doc_id}")
async def get_document(doc_id: str):
    """
    获取文档信息
    
    Args:
        doc_id: 文档 ID
        
    Returns:
        文档信息
    """
    try:
        client = get_client()
        
        doc = await client.get_document(doc_id)
        
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return {
            "success": True,
            "document": doc.dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get document: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get document: {str(e)}")


@router.get("/test")
async def test_connection():
    """
    测试飞书 API 连接
    
    Returns:
        测试结果
    """
    try:
        client = get_client()
        success = await client.test_connection()
        
        if success:
            logger.info("Feishu API connection test successful")
            return {
                "success": True,
                "message": "Successfully connected to Feishu API"
            }
        else:
            logger.warning("Feishu API connection test failed")
            return {
                "success": False,
                "message": "Failed to connect to Feishu API"
            }
            
    except Exception as e:
        logger.error(f"Feishu API connection test failed: {e}")
        return {
            "success": False,
            "message": f"Connection test failed: {str(e)}"
        }


@router.on_event("startup")
async def startup_event():
    """启动事件"""
    try:
        manager = get_manager()
        await manager.initialize()
        logger.info("Feishu Bot Manager initialized")
    except Exception as e:
        logger.error(f"Failed to initialize Feishu Bot Manager: {e}")
