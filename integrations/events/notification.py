"""
AgentForge Notification Service
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from loguru import logger
import asyncio
import aiohttp

from integrations.events.event_bus import Event, event_bus


class Notification(BaseModel):
    """Notification definition"""
    id: str
    type: str
    title: str
    message: str
    priority: str = "normal"
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = Field(default_factory=dict)


class NotificationService:
    """Notification service for multiple channels"""
    
    def __init__(
        self,
        telegram_token: Optional[str] = None,
        telegram_chat_id: Optional[str] = None,
        smtp_host: Optional[str] = None,
        smtp_port: int = 587,
        smtp_user: Optional[str] = None,
        smtp_password: Optional[str] = None
    ):
        self.telegram_token = telegram_token
        self.telegram_chat_id = telegram_chat_id
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        
        self._notification_counter = 0
        self._setup_event_handlers()
    
    def _generate_notification_id(self) -> str:
        self._notification_counter += 1
        return f"notif_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{self._notification_counter:04d}"
    
    def _setup_event_handlers(self) -> None:
        """Setup event handlers for notifications"""
        
        @event_bus.subscribe(["order.created", "order.updated", "order.completed"])
        async def handle_order_event(event: Event):
            await self.send_notification(
                type="order",
                title=f"Order {event.type.split('.')[1].title()}",
                message=f"Order from {event.source}: {event.data}",
                priority="high"
            )
        
        @event_bus.subscribe(["message.received", "message.sent"])
        async def handle_message_event(event: Event):
            await self.send_notification(
                type="message",
                title="New Message",
                message=event.data.get("content", ""),
                priority="normal"
            )
        
        @event_bus.subscribe(["error.occurred", "system.alert"])
        async def handle_alert_event(event: Event):
            await self.send_notification(
                type="alert",
                title="System Alert",
                message=event.data.get("message", "An error occurred"),
                priority="urgent"
            )
        
        logger.info("Notification event handlers registered")
    
    async def send_notification(
        self,
        type: str,
        title: str,
        message: str,
        priority: str = "normal",
        channels: Optional[List[str]] = None
    ) -> Notification:
        """Send notification through multiple channels"""
        
        notification = Notification(
            id=self._generate_notification_id(),
            type=type,
            title=title,
            message=message,
            priority=priority
        )
        
        channels = channels or ["desktop"]
        
        for channel in channels:
            try:
                if channel == "desktop":
                    await self._send_desktop(notification)
                elif channel == "telegram":
                    await self._send_telegram(notification)
                elif channel == "email":
                    await self._send_email(notification)
            except Exception as e:
                logger.error(f"Failed to send notification via {channel}: {e}")
        
        logger.info(f"Sent notification {notification.id}: {title}")
        return notification
    
    async def _send_desktop(self, notification: Notification) -> None:
        """Send desktop notification (placeholder)"""
        logger.info(f"Desktop notification: {notification.title} - {notification.message}")
    
    async def _send_telegram(self, notification: Notification) -> None:
        """Send Telegram notification"""
        if not self.telegram_token or not self.telegram_chat_id:
            logger.warning("Telegram not configured")
            return
        
        try:
            text = f"*{notification.title}*\n\n{notification.message}"
            
            async with aiohttp.ClientSession() as session:
                url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
                params = {
                    "chat_id": self.telegram_chat_id,
                    "text": text,
                    "parse_mode": "Markdown"
                }
                
                async with session.post(url, params=params) as response:
                    if response.status == 200:
                        logger.info(f"Telegram notification sent: {notification.id}")
                    else:
                        error = await response.text()
                        logger.error(f"Telegram API error: {error}")
                        
        except Exception as e:
            logger.error(f"Telegram notification failed: {e}")
    
    async def _send_email(self, notification: Notification) -> None:
        """Send email notification (placeholder)"""
        if not self.smtp_host or not self.smtp_user:
            logger.warning("SMTP not configured")
            return
        
        logger.info(f"Email notification: {notification.title} - {notification.message}")
    
    async def notify_order_created(self, order_data: Dict[str, Any]) -> Notification:
        """Notify about new order"""
        return await self.send_notification(
            type="order",
            title="New Order Received",
            message=f"Order #{order_data.get('id', 'unknown')} from {order_data.get('customer', 'unknown')}",
            priority="high",
            channels=["desktop", "telegram"]
        )
    
    async def notify_message_received(self, message_data: Dict[str, Any]) -> Notification:
        """Notify about new message"""
        return await self.send_notification(
            type="message",
            title="New Message",
            message=message_data.get("content", "")[:200],
            priority="normal",
            channels=["desktop"]
        )
    
    async def notify_error(self, error_data: Dict[str, Any]) -> Notification:
        """Notify about error"""
        return await self.send_notification(
            type="alert",
            title="Error Alert",
            message=error_data.get("message", "An error occurred"),
            priority="urgent",
            channels=["desktop", "telegram", "email"]
        )


notification_service = NotificationService()
