"""
AgentForge Telegram Bot Integration API
Telegram Bot API 端点
"""
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from loguru import logger

from integrations.external.telegram_bot import TelegramBot, TelegramBotManager
from integrations.external.telegram_models import (
    Notification, NotificationType, Subscriber, Message,
    SendMessageRequest, BotInfo
)

router = APIRouter(prefix="/api/telegram", tags=["telegram"])

# 全局 Bot 实例
_bot: Optional[TelegramBot] = None
_manager: Optional[TelegramBotManager] = None


def get_bot() -> TelegramBot:
    """获取 Bot 实例"""
    global _bot
    if _bot is None:
        _bot = TelegramBot()
    return _bot


def get_manager() -> TelegramBotManager:
    """获取 Bot 管理器实例"""
    global _manager
    if _manager is None:
        _manager = TelegramBotManager(get_bot())
    return _manager


class WebhookRequest(BaseModel):
    """Webhook 请求"""
    update_id: int
    message: Optional[Dict[str, Any]] = None
    callback_query: Optional[Dict[str, Any]] = None


class NotificationSendRequest(BaseModel):
    """发送通知请求"""
    chat_id: int
    notification_type: NotificationType
    title: str
    message: str
    data: Optional[Dict[str, Any]] = None


class SubscribeRequest(BaseModel):
    """订阅请求"""
    chat_id: int
    user_id: int
    username: Optional[str] = None
    first_name: str = "User"
    notification_types: List[NotificationType] = Field(default_factory=list)


class BroadcastRequest(BaseModel):
    """广播请求"""
    notification_type: NotificationType
    title: str
    message: str
    data: Optional[Dict[str, Any]] = None


@router.get("/info")
async def get_bot_info():
    """
    获取机器人信息
    
    Returns:
        机器人信息
    """
    try:
        bot = get_bot()
        bot_info = await bot.get_me()
        
        if not bot_info:
            raise HTTPException(status_code=500, detail="Failed to get bot info")
        
        logger.info(f"Retrieved bot info: @{bot_info.username}")
        
        return {
            "success": True,
            "bot": bot_info.dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get bot info: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get bot info: {str(e)}")


@router.post("/webhook")
async def webhook(request: WebhookRequest, background_tasks: BackgroundTasks):
    """
    Telegram Webhook 端点
    
    Args:
        request: Webhook 请求数据
        background_tasks: 后台任务
        
    Returns:
        处理结果
    """
    try:
        manager = get_manager()
        bot = get_bot()
        
        # 处理消息
        if request.message:
            message_data = request.message
            message = bot._parse_message(message_data)
            
            # 在后台处理消息
            background_tasks.add_task(bot.handle_message, message)
        
        # 处理回调查询
        if request.callback_query:
            # TODO: 实现回调处理
            pass
        
        return {"success": True, "message": "Update received"}
        
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        raise HTTPException(status_code=500, detail=f"Webhook error: {str(e)}")


@router.post("/send-message")
async def send_message(request: SendMessageRequest):
    """
    发送文本消息
    
    Args:
        request: 发送请求
        
    Returns:
        发送结果
    """
    try:
        bot = get_bot()
        
        message = await bot.send_message(
            chat_id=request.chat_id,
            text=request.text,
            parse_mode=request.parse_mode,
            disable_web_page_preview=request.disable_web_page_preview,
            disable_notification=request.disable_notification,
            reply_to_message_id=request.reply_to_message_id
        )
        
        if not message:
            raise HTTPException(status_code=500, detail="Failed to send message")
        
        logger.info(f"Message sent to chat {request.chat_id}")
        
        return {
            "success": True,
            "message_id": message.message_id,
            "chat_id": request.chat_id
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
        bot = get_bot()
        
        notification = Notification(
            id=f"notif_{datetime.now().timestamp()}",
            type=request.notification_type,
            title=request.title,
            message=request.message,
            chat_id=request.chat_id,
            data=request.data
        )
        
        success = await bot.send_notification(notification)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to send notification")
        
        logger.info(f"Notification sent to chat {request.chat_id}")
        
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
        manager = get_manager()
        bot = get_bot()
        
        notification = Notification(
            id=f"notif_{datetime.now().timestamp()}",
            type=request.notification_type,
            title=request.title,
            message=request.message,
            chat_id=0,
            data=request.data
        )
        
        # 获取所有订阅者
        subscribers = manager._subscribers
        
        stats = await bot.broadcast_notification(notification, subscribers)
        
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
            # 更新订阅
            existing.subscribed_types = request.notification_types or list(NotificationType)
            existing.enabled = True
            logger.info(f"Updated subscription for user {request.user_id}")
        else:
            # 新订阅
            subscriber = Subscriber(
                user_id=request.user_id,
                chat_id=request.chat_id,
                username=request.username,
                first_name=request.first_name,
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
async def unsubscribe(user_id: int = Query(..., description="用户 ID")):
    """
    取消订阅
    
    Args:
        user_id: 用户 ID
        
    Returns:
        取消结果
    """
    try:
        manager = get_manager()
        
        # 移除订阅者
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


@router.post("/webhook/set")
async def set_webhook(url: str = Query(..., description="Webhook URL")):
    """
    设置 Webhook
    
    Args:
        url: Webhook URL
        
    Returns:
        设置结果
    """
    try:
        bot = get_bot()
        
        success = await bot.set_webhook(url=url)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to set webhook")
        
        logger.info(f"Webhook set to: {url}")
        
        return {
            "success": True,
            "url": url
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to set webhook: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to set webhook: {str(e)}")


@router.post("/webhook/delete")
async def delete_webhook():
    """
    删除 Webhook
    
    Returns:
        删除结果
    """
    try:
        bot = get_bot()
        
        success = await bot.delete_webhook()
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete webhook")
        
        logger.info("Webhook deleted")
        
        return {
            "success": True,
            "message": "Webhook deleted"
        }
        
    except Exception as e:
        logger.error(f"Failed to delete webhook: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete webhook: {str(e)}")


@router.get("/webhook/info")
async def get_webhook_info():
    """
    获取 Webhook 信息
    
    Returns:
        Webhook 信息
    """
    try:
        bot = get_bot()
        
        webhook_info = await bot.get_webhook_info()
        
        if not webhook_info:
            raise HTTPException(status_code=404, detail="Webhook info not available")
        
        return {
            "success": True,
            "webhook": webhook_info.dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get webhook info: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get webhook info: {str(e)}")


@router.get("/test")
async def test_connection():
    """
    测试 Telegram Bot 连接
    
    Returns:
        测试结果
    """
    try:
        bot = get_bot()
        success = await bot.test_connection()
        
        if success:
            logger.info("Telegram Bot connection test successful")
            return {
                "success": True,
                "message": "Successfully connected to Telegram Bot API"
            }
        else:
            logger.warning("Telegram Bot connection test failed")
            return {
                "success": False,
                "message": "Failed to connect to Telegram Bot API"
            }
            
    except Exception as e:
        logger.error(f"Telegram Bot connection test failed: {e}")
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
        logger.info("Telegram Bot Manager initialized")
    except Exception as e:
        logger.error(f"Failed to initialize Telegram Bot Manager: {e}")
