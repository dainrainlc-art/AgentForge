"""
AgentForge Feishu (Lark) Integration Client
飞书 API 客户端实现
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import httpx
import hashlib
import base64
import hmac
from loguru import logger

from agentforge.config import settings
from integrations.external.feishu_models import (
    User, Chat, Message, Notification, NotificationType, Subscriber,
    CalendarEvent, Document, FeishuResponse, FeishuError,
    DEFAULT_NOTIFICATION_TEMPLATES, MessageType
)


class FeishuClient:
    """飞书 API 客户端"""
    
    BASE_URL = "https://open.feishu.cn/open-apis"
    
    def __init__(
        self,
        app_id: Optional[str] = None,
        app_secret: Optional[str] = None,
        verification_token: Optional[str] = None
    ):
        """
        初始化飞书客户端
        
        Args:
            app_id: 应用 App ID
            app_secret: 应用 App Secret
            verification_token: 事件订阅验证 Token
        """
        self.app_id = app_id or getattr(settings, 'feishu_app_id', None)
        self.app_secret = app_secret or getattr(settings, 'feishu_app_secret', None)
        self.verification_token = verification_token or getattr(settings, 'feishu_verification_token', None)
        
        self._tenant_access_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
    
    def _get_headers(self, use_tenant_token: bool = True) -> Dict[str, str]:
        """获取请求头"""
        headers = {
            "Content-Type": "application/json"
        }
        
        if use_tenant_token and self._tenant_access_token:
            headers["Authorization"] = f"Bearer {self._tenant_access_token}"
        
        return headers
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        use_tenant_token: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        发送 HTTP 请求
        
        Args:
            method: HTTP 方法
            endpoint: API 端点
            params: 查询参数
            json: JSON 数据
            use_tenant_token: 是否使用 tenant_access_token
            
        Returns:
            API 响应数据
        """
        if not self.app_id or not self.app_secret:
            logger.error("Feishu credentials not configured")
            return None
        
        # 确保有有效的 token
        if use_tenant_token:
            await self._ensure_tenant_access_token()
        
        url = f"{self.BASE_URL}{endpoint}"
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=self._get_headers(use_tenant_token),
                    params=params,
                    json=json
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("code") == 0:
                        return data.get("data")
                    else:
                        logger.error(f"Feishu API error: {data}")
                        return None
                else:
                    logger.error(f"HTTP error: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Feishu request failed: {e}")
            return None
    
    async def _ensure_tenant_access_token(self):
        """确保有有效的 tenant_access_token"""
        if self._tenant_access_token and self._token_expires_at:
            if datetime.now() < self._token_expires_at:
                return
        
        # 获取新的 token
        await self._get_tenant_access_token()
    
    async def _get_tenant_access_token(self):
        """获取 tenant_access_token"""
        json_data = {
            "app_id": self.app_id,
            "app_secret": self.app_secret
        }
        
        data = await self._request(
            "POST",
            "/auth/v3/tenant_access_token/internal",
            json=json_data,
            use_tenant_token=False
        )
        
        if data:
            self._tenant_access_token = data.get("tenant_access_token")
            expires_in = data.get("expire", 7200)
            self._token_expires_at = datetime.now() + timedelta(seconds=expires_in - 60)
            logger.info("Successfully obtained tenant_access_token")
    
    # ========== 用户管理 ==========
    
    async def get_user_info(self, user_id: str) -> Optional[User]:
        """
        获取用户信息
        
        Args:
            user_id: 用户 ID
            
        Returns:
            用户信息
        """
        data = await self._request("GET", f"/contact/v3/users/{user_id}")
        
        if not data or "user" not in data:
            return None
        
        user_data = data["user"]
        
        return User(
            user_id=user_data.get("user_id", ""),
            open_id=user_data.get("open_id", ""),
            union_id=user_data.get("union_id", ""),
            name=user_data.get("name", ""),
            en_name=user_data.get("en_name"),
            nickname=user_data.get("nickname"),
            email=user_data.get("email"),
            mobile=user_data.get("mobile"),
            gender=user_data.get("gender", 0),
            avatar=user_data.get("avatar", {}).get("avatar_72"),
            avatar_thumb=user_data.get("avatar", {}).get("avatar_thumb"),
            avatar_middle=user_data.get("avatar", {}).get("avatar_middle"),
            avatar_large=user_data.get("avatar", {}).get("avatar_large"),
            status=user_data.get("status", {}).get("is_activated", 0),
            department_ids=user_data.get("department_ids", []),
            job_number=user_data.get("job_number"),
            employee_type=user_data.get("employee_type", 0)
        )
    
    async def search_user(self, email: str) -> Optional[User]:
        """
        通过邮箱搜索用户
        
        Args:
            email: 邮箱地址
            
        Returns:
            用户信息
        """
        json_data = {
            "emails": [email]
        }
        
        data = await self._request(
            "POST",
            "/contact/v3/users/batch_get_id",
            json=json_data
        )
        
        if not data or "user_infos" not in data:
            return None
        
        if data["user_infos"]:
            user_id = data["user_infos"][0].get("user_id")
            return await self.get_user_info(user_id)
        
        return None
    
    # ========== 消息发送 ==========
    
    async def send_message(
        self,
        chat_id: str,
        content: str,
        message_type: MessageType = MessageType.TEXT,
        receive_id: Optional[str] = None,
        msg_type: str = "receive_id"
    ) -> Optional[Message]:
        """
        发送消息
        
        Args:
            chat_id: 聊天 ID
            content: 消息内容
            message_type: 消息类型
            receive_id: 接收者 ID
            msg_type: ID 类型
            
        Returns:
            发送的消息
        """
        json_data = {
            "receive_id": receive_id or chat_id,
            "content": content,
            "msg_type": msg_type
        }
        
        data = await self._request(
            "POST",
            f"/im/v1/messages",
            json=json_data
        )
        
        if not data:
            return None
        
        return Message(
            message_id=data.get("message_id", ""),
            chat_id=chat_id,
            sender_id=data.get("sender_id", ""),
            content=content,
            message_type=message_type,
            create_time=datetime.fromtimestamp(data.get("create_time", 0) / 1000) if data.get("create_time") else datetime.now()
        )
    
    async def send_text_message(
        self,
        chat_id: str,
        text: str,
        receive_id: Optional[str] = None
    ) -> Optional[Message]:
        """
        发送文本消息
        
        Args:
            chat_id: 聊天 ID
            text: 消息文本
            receive_id: 接收者 ID
            
        Returns:
            发送的消息
        """
        content = f'{{"text": "{text}"}}'
        return await self.send_message(
            chat_id=chat_id,
            content=content,
            message_type=MessageType.TEXT,
            receive_id=receive_id
        )
    
    async def send_post_message(
        self,
        chat_id: str,
        content: Dict[str, Any],
        receive_id: Optional[str] = None
    ) -> Optional[Message]:
        """
        发送富文本消息
        
        Args:
            chat_id: 聊天 ID
            content: 富文本内容
            receive_id: 接收者 ID
            
        Returns:
            发送的消息
        """
        import json
        return await self.send_message(
            chat_id=chat_id,
            content=json.dumps(content),
            message_type=MessageType.POST,
            receive_id=receive_id
        )
    
    async def send_interactive_card(
        self,
        chat_id: str,
        card: Dict[str, Any],
        receive_id: Optional[str] = None
    ) -> Optional[Message]:
        """
        发送交互式卡片消息
        
        Args:
            chat_id: 聊天 ID
            card: 卡片配置
            receive_id: 接收者 ID
            
        Returns:
            发送的消息
        """
        import json
        return await self.send_message(
            chat_id=chat_id,
            content=json.dumps(card),
            message_type=MessageType.INTERACTIVE,
            receive_id=receive_id
        )
    
    # ========== 通知系统 ==========
    
    async def send_notification(
        self,
        notification: Notification
    ) -> bool:
        """
        发送通知
        
        Args:
            notification: 通知对象
            
        Returns:
            是否成功
        """
        template = DEFAULT_NOTIFICATION_TEMPLATES.get(notification.type)
        
        if template:
            title = template["title"]
            content = template["content"]
            
            # 替换模板变量
            if notification.data:
                try:
                    title = title.format(**notification.data)
                    content = content.format(**notification.data)
                except KeyError as e:
                    logger.error(f"Missing template variable: {e}")
            
            full_content = f"**{title}**\n\n{content}"
        else:
            full_content = f"**{notification.title}**\n\n{notification.content}"
        
        receive_id = notification.receiver_id
        msg_type = "open_id" if notification.receiver_type == "user" else "chat_id"
        
        result = await self.send_message(
            chat_id=notification.receiver_id,
            content=f'{{"text": "{full_content}"}}',
            message_type=MessageType.TEXT,
            receive_id=receive_id,
            msg_type=msg_type
        )
        
        if result:
            notification.sent = True
            notification.sent_at = datetime.now()
            logger.info(f"Notification sent to {notification.receiver_id}")
            return True
        else:
            logger.error(f"Failed to send notification to {notification.receiver_id}")
            return False
    
    async def broadcast_notification(
        self,
        notification: Notification,
        subscribers: List[Subscriber]
    ) -> Dict[str, int]:
        """
        广播通知给所有订阅者
        
        Args:
            notification: 通知对象
            subscribers: 订阅者列表
            
        Returns:
            统计信息
        """
        stats = {"sent": 0, "failed": 0}
        
        for subscriber in subscribers:
            if not subscriber.enabled:
                continue
            
            if notification.type not in subscriber.subscribed_types:
                continue
            
            notification.receiver_id = subscriber.open_id
            notification.receiver_type = "user"
            success = await self.send_notification(notification)
            
            if success:
                stats["sent"] += 1
            else:
                stats["failed"] += 1
        
        logger.info(f"Broadcast completed: {stats['sent']} sent, {stats['failed']} failed")
        return stats
    
    # ========== 日历管理 ==========
    
    async def create_calendar_event(
        self,
        event: CalendarEvent,
        calendar_id: str = "primary"
    ) -> Optional[CalendarEvent]:
        """
        创建日历事件
        
        Args:
            event: 事件信息
            calendar_id: 日历 ID
            
        Returns:
            创建的事件
        """
        json_data = {
            "summary": event.summary,
            "description": event.description,
            "start_time": {
                "timestamp": int(event.start_time.timestamp()),
                "timezone": event.timezone
            },
            "end_time": {
                "timestamp": int(event.end_time.timestamp()),
                "timezone": event.timezone
            },
            "location": event.location,
            "attendees": [{"user_id": uid} for uid in event.attendee_ids],
            "reminders": {"use_default": False, "reminders": [{"minutes": m} for m in event.reminders]}
        }
        
        data = await self._request(
            "POST",
            f"/calendar/v4/calendars/{calendar_id}/events",
            json=json_data
        )
        
        if not data:
            return None
        
        return CalendarEvent(
            event_id=data.get("event_id", ""),
            summary=event.summary,
            description=event.description,
            start_time=event.start_time,
            end_time=event.end_time,
            timezone=event.timezone,
            location=event.location,
            organizer_id=event.organizer_id,
            attendee_ids=event.attendee_ids,
            status="confirmed"
        )
    
    async def get_calendar_events(
        self,
        time_min: datetime,
        time_max: datetime,
        calendar_id: str = "primary"
    ) -> List[CalendarEvent]:
        """
        获取日历事件
        
        Args:
            time_min: 开始时间
            time_max: 结束时间
            calendar_id: 日历 ID
            
        Returns:
            事件列表
        """
        params = {
            "time_min": int(time_min.timestamp()),
            "time_max": int(time_max.timestamp())
        }
        
        data = await self._request(
            "GET",
            f"/calendar/v4/calendars/{calendar_id}/events",
            params=params
        )
        
        if not data or "items" not in data:
            return []
        
        events = []
        for item in data["items"]:
            event = CalendarEvent(
                event_id=item.get("event_id", ""),
                summary=item.get("summary", ""),
                description=item.get("description", ""),
                start_time=datetime.fromtimestamp(item.get("start_time", {}).get("timestamp", 0)),
                end_time=datetime.fromtimestamp(item.get("end_time", {}).get("timestamp", 0)),
                organizer_id=item.get("organizer_id", ""),
                status=item.get("status", "confirmed")
            )
            events.append(event)
        
        return events
    
    # ========== 文档管理 ==========
    
    async def get_document(self, doc_id: str) -> Optional[Document]:
        """
        获取文档信息
        
        Args:
            doc_id: 文档 ID
            
        Returns:
            文档信息
        """
        data = await self._request("GET", f"/docx/v1/documents/{doc_id}")
        
        if not data:
            return None
        
        return Document(
            doc_id=data.get("document_id", ""),
            title=data.get("title", ""),
            doc_type=data.get("doc_type", "doc"),
            owner_id=data.get("owner_id", ""),
            create_time=datetime.fromtimestamp(data.get("create_time", 0) / 1000) if data.get("create_time") else datetime.now(),
            update_time=datetime.fromtimestamp(data.get("update_time", 0) / 1000) if data.get("update_time") else datetime.now(),
            url=data.get("url", "")
        )
    
    # ========== Webhook 验证 ==========
    
    def verify_webhook_signature(
        self,
        signature: str,
        timestamp: str,
        body: str
    ) -> bool:
        """
        验证 Webhook 签名
        
        Args:
            signature: 签名
            timestamp: 时间戳
            body: 请求体
            
        Returns:
            是否有效
        """
        if not self.verification_token:
            logger.warning("Verification token not configured")
            return False
        
        # 构建待签名字符串
        string_to_sign = timestamp + self.verification_token + body
        signature_computed = base64.b64encode(
            hmac.new(
                self.verification_token.encode(),
                string_to_sign.encode(),
                hashlib.sha256
            ).digest()
        ).decode()
        
        return signature == signature_computed
    
    async def test_connection(self) -> bool:
        """测试连接"""
        # 尝试获取当前用户信息
        data = await self._request("GET", "/auth/v3/user_info")
        return data is not None


class FeishuBotManager:
    """飞书 Bot 管理器 - 高级封装"""
    
    def __init__(self, client: Optional[FeishuClient] = None):
        """
        初始化 Bot 管理器
        
        Args:
            client: 飞书客户端
        """
        self.client = client or FeishuClient()
        self._subscribers: List[Subscriber] = []
    
    async def initialize(self):
        """初始化"""
        if await self.client.test_connection():
            logger.info("Connected to Feishu API")
    
    async def send_system_notification(
        self,
        notification_type: NotificationType,
        title: str,
        content: str,
        receiver_id: str,
        data: Optional[Dict[str, Any]] = None
    ):
        """
        发送系统通知
        
        Args:
            notification_type: 通知类型
            title: 标题
            content: 内容
            receiver_id: 接收者 ID
            data: 模板数据
        """
        notification = Notification(
            id=f"notif_{datetime.now().timestamp()}",
            type=notification_type,
            title=title,
            content=content,
            receiver_id=receiver_id,
            receiver_type="user",
            data=data
        )
        
        await self.client.send_notification(notification)
    
    async def notify_task_created(self, task_id: str, task_type: str, description: str, user_id: str):
        """通知任务创建"""
        await self.send_system_notification(
            NotificationType.TASK_CREATED,
            "新任务创建",
            f"任务 ID: {task_id}",
            user_id,
            data={
                "task_id": task_id,
                "task_type": task_type,
                "description": description
            }
        )
    
    async def notify_task_completed(self, task_id: str, task_type: str, result: str, user_id: str):
        """通知任务完成"""
        await self.send_system_notification(
            NotificationType.TASK_COMPLETED,
            "任务完成",
            f"任务 ID: {task_id}",
            user_id,
            data={
                "task_id": task_id,
                "task_type": task_type,
                "result": result
            }
        )
    
    async def notify_error(self, error: str, level: str, user_id: str):
        """通知错误"""
        await self.send_system_notification(
            NotificationType.ERROR_ALERT,
            "错误警报",
            f"错误：{error}",
            user_id,
            data={
                "error": error,
                "level": level,
                "timestamp": datetime.now().isoformat()
            }
        )
    
    async def notify_meeting_reminder(
        self,
        meeting_title: str,
        start_time: datetime,
        location: str,
        user_id: str
    ):
        """通知会议提醒"""
        await self.send_system_notification(
            NotificationType.MEETING_REMINDER,
            "会议提醒",
            f"会议：{meeting_title}",
            user_id,
            data={
                "meeting_title": meeting_title,
                "start_time": start_time.strftime("%Y-%m-%d %H:%M"),
                "location": location
            }
        )
