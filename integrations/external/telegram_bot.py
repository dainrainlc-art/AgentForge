"""
AgentForge Telegram Bot Integration Client
Telegram Bot API 客户端实现
"""
from typing import Optional, List, Dict, Any, Callable, Awaitable
from datetime import datetime
import httpx
import asyncio
from loguru import logger

from agentforge.config import settings
from integrations.external.telegram_models import (
    User, Chat, Message, CallbackQuery, InlineQuery, Update,
    BotCommand, Notification, NotificationType, Subscriber,
    SendMessageRequest, SendPhotoRequest, SendDocumentRequest,
    TelegramResponse, TelegramError, BotInfo, WebhookInfo,
    DEFAULT_NOTIFICATION_TEMPLATES, MessageType
)


class TelegramBot:
    """Telegram Bot API 客户端"""
    
    BASE_URL = "https://api.telegram.org/bot"
    
    def __init__(self, token: Optional[str] = None):
        """
        初始化 Telegram Bot 客户端
        
        Args:
            token: Bot Token（从 @BotFather 获取）
        """
        self.token = token or getattr(settings, 'telegram_bot_token', None)
        
        if not self.token:
            logger.warning("Telegram bot token not configured")
        
        self._webhook_url: Optional[str] = None
        self._message_handlers: Dict[str, Callable[[Message], Awaitable[None]]] = {}
        self._command_handlers: Dict[str, Callable[[Message], Awaitable[None]]] = {}
        self._callback_handlers: Dict[str, Callable[[CallbackQuery], Awaitable[None]]] = {}
        
        self._running = False
        self._polling_task: Optional[asyncio.Task] = None
    
    def _get_url(self, endpoint: str) -> str:
        """获取完整的 API URL"""
        return f"{self.BASE_URL}{self.token}/{endpoint}"
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        发送 HTTP 请求
        
        Args:
            method: HTTP 方法
            endpoint: API 端点
            params: 查询参数
            json: JSON 数据
            
        Returns:
            API 响应数据
        """
        if not self.token:
            logger.error("Telegram bot token not configured")
            return None
        
        url = self._get_url(endpoint)
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("ok"):
                        return data.get("result")
                    else:
                        logger.error(f"Telegram API error: {data}")
                        return None
                else:
                    logger.error(f"HTTP error: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Telegram request failed: {e}")
            return None
    
    # ========== 基础信息 ==========
    
    async def get_me(self) -> Optional[BotInfo]:
        """
        获取机器人信息
        
        Returns:
            机器人信息
        """
        data = await self._request("GET", "getMe")
        
        if not data:
            return None
        
        return BotInfo(
            id=data["id"],
            is_bot=data["is_bot"],
            first_name=data["first_name"],
            username=data["username"],
            can_join_groups=data.get("can_join_groups", False),
            can_read_all_group_messages=data.get("can_read_all_group_messages", False),
            supports_inline_queries=data.get("supports_inline_queries", False)
        )
    
    async def get_updates(
        self,
        offset: Optional[int] = None,
        limit: int = 100,
        timeout: int = 30,
        allowed_updates: Optional[List[str]] = None
    ) -> List[Update]:
        """
        获取更新（长轮询）
        
        Args:
            offset: 更新偏移量
            limit: 返回数量
            timeout: 超时时间（秒）
            allowed_updates: 允许的更新类型
            
        Returns:
            更新列表
        """
        params = {
            "offset": offset,
            "limit": limit,
            "timeout": timeout
        }
        
        if allowed_updates:
            params["allowed_updates"] = allowed_updates
        
        data = await self._request("POST", "getUpdates", json=params)
        
        if not data:
            return []
        
        updates = []
        for item in data:
            update = self._parse_update(item)
            if update:
                updates.append(update)
        
        return updates
    
    def _parse_update(self, data: Dict[str, Any]) -> Optional[Update]:
        """解析更新数据"""
        try:
            return Update(**data)
        except Exception as e:
            logger.error(f"Failed to parse update: {e}")
            return None
    
    # ========== 消息发送 ==========
    
    async def send_message(
        self,
        chat_id: int,
        text: str,
        parse_mode: Optional[str] = None,
        disable_web_page_preview: bool = False,
        disable_notification: bool = False,
        reply_to_message_id: Optional[int] = None
    ) -> Optional[Message]:
        """
        发送文本消息
        
        Args:
            chat_id: 聊天 ID
            text: 消息文本
            parse_mode: 解析模式（HTML, Markdown, MarkdownV2）
            disable_web_page_preview: 禁用网页预览
            disable_notification: 静音发送
            reply_to_message_id: 回复的消息 ID
            
        Returns:
            发送的消息
        """
        json_data = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": disable_web_page_preview,
            "disable_notification": disable_notification,
            "reply_to_message_id": reply_to_message_id
        }
        
        # 移除 None 值
        json_data = {k: v for k, v in json_data.items() if v is not None}
        
        data = await self._request("POST", "sendMessage", json=json_data)
        
        if not data:
            return None
        
        return self._parse_message(data)
    
    def _parse_message(self, data: Dict[str, Any]) -> Message:
        """解析消息数据"""
        chat = Chat(
            id=data["chat"]["id"],
            type=data["chat"]["type"],
            title=data["chat"].get("title"),
            username=data["chat"].get("username")
        )
        
        from_user = None
        if "from" in data:
            from_user = User(
                id=data["from"]["id"],
                is_bot=data["from"].get("is_bot", False),
                first_name=data["from"]["first_name"],
                last_name=data["from"].get("last_name"),
                username=data["from"].get("username")
            )
        
        message = Message(
            message_id=data["message_id"],
            chat=chat,
            from_user=from_user,
            date=datetime.fromtimestamp(data["date"]),
            text=data.get("text"),
            message_type=self._detect_message_type(data)
        )
        
        return message
    
    def _detect_message_type(self, data: Dict[str, Any]) -> MessageType:
        """检测消息类型"""
        if "photo" in data:
            return MessageType.PHOTO
        elif "video" in data:
            return MessageType.VIDEO
        elif "audio" in data:
            return MessageType.AUDIO
        elif "document" in data:
            return MessageType.DOCUMENT
        elif "sticker" in data:
            return MessageType.STICKER
        elif "location" in data:
            return MessageType.LOCATION
        elif "contact" in data:
            return MessageType.CONTACT
        else:
            return MessageType.TEXT
    
    async def send_photo(
        self,
        chat_id: int,
        photo: str,
        caption: Optional[str] = None,
        parse_mode: Optional[str] = None,
        disable_notification: bool = False,
        reply_to_message_id: Optional[int] = None
    ) -> Optional[Message]:
        """
        发送照片
        
        Args:
            chat_id: 聊天 ID
            photo: 照片 URL 或 file_id
            caption: 说明文字
            parse_mode: 解析模式
            disable_notification: 静音发送
            reply_to_message_id: 回复的消息 ID
            
        Returns:
            发送的消息
        """
        json_data = {
            "chat_id": chat_id,
            "photo": photo,
            "caption": caption,
            "parse_mode": parse_mode,
            "disable_notification": disable_notification,
            "reply_to_message_id": reply_to_message_id
        }
        
        json_data = {k: v for k, v in json_data.items() if v is not None}
        
        data = await self._request("POST", "sendPhoto", json=json_data)
        
        if not data:
            return None
        
        return self._parse_message(data)
    
    async def send_document(
        self,
        chat_id: int,
        document: str,
        caption: Optional[str] = None,
        parse_mode: Optional[str] = None,
        disable_notification: bool = False,
        reply_to_message_id: Optional[int] = None
    ) -> Optional[Message]:
        """
        发送文档
        
        Args:
            chat_id: 聊天 ID
            document: 文档 URL 或 file_id
            caption: 说明文字
            parse_mode: 解析模式
            disable_notification: 静音发送
            reply_to_message_id: 回复的消息 ID
            
        Returns:
            发送的消息
        """
        json_data = {
            "chat_id": chat_id,
            "document": document,
            "caption": caption,
            "parse_mode": parse_mode,
            "disable_notification": disable_notification,
            "reply_to_message_id": reply_to_message_id
        }
        
        json_data = {k: v for k, v in json_data.items() if v is not None}
        
        data = await self._request("POST", "sendDocument", json=json_data)
        
        if not data:
            return None
        
        return self._parse_message(data)
    
    async def edit_message_text(
        self,
        text: str,
        chat_id: Optional[int] = None,
        message_id: Optional[int] = None,
        inline_message_id: Optional[str] = None,
        parse_mode: Optional[str] = None,
        disable_web_page_preview: bool = False
    ) -> Optional[Message]:
        """
        编辑消息文本
        
        Args:
            text: 新文本
            chat_id: 聊天 ID
            message_id: 消息 ID
            inline_message_id: 内联消息 ID
            parse_mode: 解析模式
            disable_web_page_preview: 禁用网页预览
            
        Returns:
            编辑后的消息
        """
        json_data = {
            "text": text,
            "chat_id": chat_id,
            "message_id": message_id,
            "inline_message_id": inline_message_id,
            "parse_mode": parse_mode,
            "disable_web_page_preview": disable_web_page_preview
        }
        
        json_data = {k: v for k, v in json_data.items() if v is not None}
        
        data = await self._request("POST", "editMessageText", json=json_data)
        
        if not data:
            return None
        
        return self._parse_message(data)
    
    async def delete_message(self, chat_id: int, message_id: int) -> bool:
        """
        删除消息
        
        Args:
            chat_id: 聊天 ID
            message_id: 消息 ID
            
        Returns:
            是否成功
        """
        json_data = {
            "chat_id": chat_id,
            "message_id": message_id
        }
        
        data = await self._request("POST", "deleteMessage", json=json_data)
        return data is not None
    
    # ========== 命令处理 ==========
    
    def register_command(self, command: str, handler: Callable[[Message], Awaitable[None]]):
        """
        注册命令处理器
        
        Args:
            command: 命令（不含 /）
            handler: 处理器函数
        """
        self._command_handlers[command] = handler
        logger.info(f"Registered command handler: /{command}")
    
    async def handle_message(self, message: Message):
        """
        处理收到的消息
        
        Args:
            message: 消息对象
        """
        if message.text and message.text.startswith("/"):
            # 处理命令
            parts = message.text.split()
            command = parts[0][1:]  # 移除 /
            
            if command in self._command_handlers:
                try:
                    await self._command_handlers[command](message)
                except Exception as e:
                    logger.error(f"Error handling command /{command}: {e}")
            else:
                # 未知命令
                await self.send_message(
                    chat_id=message.chat.id,
                    text=f"❌ 未知命令：/{command}\n使用 /help 查看可用命令"
                )
        else:
            # 处理普通消息
            for handler in self._message_handlers.values():
                try:
                    await handler(message)
                except Exception as e:
                    logger.error(f"Error handling message: {e}")
    
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
            title = template.title_template
            message = template.message_template
            
            # 替换模板变量
            if notification.data:
                try:
                    title = title.format(**notification.data)
                    message = message.format(**notification.data)
                except KeyError as e:
                    logger.error(f"Missing template variable: {e}")
            
            full_text = f"<b>{title}</b>\n\n{message}"
        else:
            full_text = f"<b>{notification.title}</b>\n\n{notification.message}"
        
        result = await self.send_message(
            chat_id=notification.chat_id,
            text=full_text,
            parse_mode="HTML"
        )
        
        if result:
            notification.sent = True
            notification.sent_at = datetime.now()
            logger.info(f"Notification sent to chat {notification.chat_id}")
            return True
        else:
            logger.error(f"Failed to send notification to chat {notification.chat_id}")
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
            
            notification.chat_id = subscriber.chat_id
            success = await self.send_notification(notification)
            
            if success:
                stats["sent"] += 1
            else:
                stats["failed"] += 1
        
        logger.info(f"Broadcast completed: {stats['sent']} sent, {stats['failed']} failed")
        return stats
    
    # ========== Webhook ==========
    
    async def set_webhook(
        self,
        url: str,
        certificate: Optional[str] = None,
        ip_address: Optional[str] = None,
        max_connections: int = 40,
        allowed_updates: Optional[List[str]] = None
    ) -> bool:
        """
        设置 Webhook
        
        Args:
            url: Webhook URL
            certificate: 证书文件路径
            ip_address: 固定的 IP 地址
            max_connections: 最大连接数
            allowed_updates: 允许的更新类型
            
        Returns:
            是否成功
        """
        json_data = {
            "url": url,
            "max_connections": max_connections
        }
        
        if certificate:
            json_data["certificate"] = certificate
        if ip_address:
            json_data["ip_address"] = ip_address
        if allowed_updates:
            json_data["allowed_updates"] = allowed_updates
        
        json_data = {k: v for k, v in json_data.items() if v is not None}
        
        data = await self._request("POST", "setWebhook", json=json_data)
        
        if data:
            self._webhook_url = url
            logger.info(f"Webhook set to: {url}")
            return True
        else:
            logger.error("Failed to set webhook")
            return False
    
    async def delete_webhook(self) -> bool:
        """删除 Webhook"""
        data = await self._request("POST", "deleteWebhook")
        
        if data:
            self._webhook_url = None
            logger.info("Webhook deleted")
            return True
        else:
            return False
    
    async def get_webhook_info(self) -> Optional[WebhookInfo]:
        """获取 Webhook 信息"""
        data = await self._request("GET", "getWebhookInfo")
        
        if not data:
            return None
        
        return WebhookInfo(
            url=data["url"],
            has_custom_certificate=data.get("has_custom_certificate", False),
            pending_update_count=data.get("pending_update_count", 0),
            ip_address=data.get("ip_address"),
            last_error_date=datetime.fromtimestamp(data["last_error_date"]) if data.get("last_error_date") else None,
            last_error_message=data.get("last_error_message"),
            max_connections=data.get("max_connections", 40),
            allowed_updates=data.get("allowed_updates", [])
        )
    
    # ========== 轮询 ==========
    
    async def start_polling(self, interval: int = 1):
        """
        启动轮询
        
        Args:
            interval: 轮询间隔（秒）
        """
        self._running = True
        logger.info("Starting polling...")
        
        offset = None
        
        while self._running:
            try:
                updates = await self.get_updates(offset=offset, timeout=30)
                
                for update in updates:
                    offset = update.update_id + 1
                    
                    if update.message:
                        await self.handle_message(update.message)
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"Polling error: {e}")
                await asyncio.sleep(5)
    
    async def stop_polling(self):
        """停止轮询"""
        self._running = False
        logger.info("Polling stopped")
    
    async def test_connection(self) -> bool:
        """测试连接"""
        bot_info = await self.get_me()
        return bot_info is not None


class TelegramBotManager:
    """Telegram Bot 管理器 - 高级封装"""
    
    def __init__(self, bot: Optional[TelegramBot] = None):
        """
        初始化 Bot 管理器
        
        Args:
            bot: Telegram Bot 实例
        """
        self.bot = bot or TelegramBot()
        self._subscribers: List[Subscriber] = []
    
    async def initialize(self):
        """初始化"""
        bot_info = await self.bot.get_me()
        if bot_info:
            logger.info(f"Connected to Telegram Bot: @{bot_info.username}")
        
        # 注册默认命令
        self._register_default_commands()
    
    def _register_default_commands(self):
        """注册默认命令"""
        self.bot.register_command("start", self._handle_start)
        self.bot.register_command("help", self._handle_help)
        self.bot.register_command("status", self._handle_status)
        self.bot.register_command("subscribe", self._handle_subscribe)
        self.bot.register_command("unsubscribe", self._handle_unsubscribe)
    
    async def _handle_start(self, message: Message):
        """处理 /start 命令"""
        welcome_text = (
            f"👋 欢迎使用 AgentForge!\n\n"
            f"我是您的 AI 助手机器人。\n\n"
            f"可用命令：\n"
            f"/help - 查看帮助\n"
            f"/status - 查看系统状态\n"
            f"/subscribe - 订阅通知\n"
            f"/unsubscribe - 取消订阅"
        )
        
        await self.bot.send_message(
            chat_id=message.chat.id,
            text=welcome_text,
            parse_mode=None  # 不使用 HTML 解析
        )
    
    async def _handle_help(self, message: Message):
        """处理 /help 命令"""
        help_text = (
            "<b>AgentForge 帮助</b>\n\n"
            "<b>可用命令:</b>\n"
            "/start - 启动机器人\n"
            "/help - 查看帮助\n"
            "/status - 查看系统状态\n"
            "/subscribe - 订阅通知\n"
            "/unsubscribe - 取消订阅\n\n"
            "<b>通知类型:</b>\n"
            "- 系统状态\n"
            "- 任务创建/完成/失败\n"
            "- 错误警报\n"
            "- 自进化系统"
        )
        
        await self.bot.send_message(
            chat_id=message.chat.id,
            text=help_text,
            parse_mode="HTML"
        )
    
    async def _handle_status(self, message: Message):
        """处理 /status 命令"""
        # 这里应该调用系统状态 API
        status_text = (
            "<b>系统状态</b>\n\n"
            "<b>服务:</b> 运行中\n"
            "<b>自进化系统:</b> 已启用\n"
            "<b>下次记忆巩固:</b> 03:00\n"
            "<b>下次自我检查:</b> 04:00\n"
            "<b>下次任务复盘:</b> 23:00"
        )
        
        await self.bot.send_message(
            chat_id=message.chat.id,
            text=status_text,
            parse_mode="HTML"
        )
    
    async def _handle_subscribe(self, message: Message):
        """处理 /subscribe 命令"""
        # 添加订阅者
        subscriber = Subscriber(
            user_id=message.from_user.id if message.from_user else 0,
            chat_id=message.chat.id,
            username=message.from_user.username if message.from_user else None,
            first_name=message.from_user.first_name if message.from_user else "User",
            subscribed_types=list(NotificationType)
        )
        
        self._subscribers.append(subscriber)
        
        await self.bot.send_message(
            chat_id=message.chat.id,
            text="✅ 已成功订阅所有通知类型",
            parse_mode=None
        )
    
    async def _handle_unsubscribe(self, message: Message):
        """处理 /unsubscribe 命令"""
        # 移除订阅者
        user_id = message.from_user.id if message.from_user else 0
        self._subscribers = [s for s in self._subscribers if s.user_id != user_id]
        
        await self.bot.send_message(
            chat_id=message.chat.id,
            text="❌ 已取消订阅",
            parse_mode=None
        )
    
    async def send_system_notification(
        self,
        notification_type: NotificationType,
        title: str,
        message: str,
        data: Optional[Dict[str, Any]] = None
    ):
        """
        发送系统通知
        
        Args:
            notification_type: 通知类型
            title: 标题
            message: 消息内容
            data: 模板数据
        """
        notification = Notification(
            id=f"notif_{datetime.now().timestamp()}",
            type=notification_type,
            title=title,
            message=message,
            chat_id=0,  # 广播时为 0
            data=data
        )
        
        await self.bot.broadcast_notification(notification, self._subscribers)
    
    async def notify_task_created(self, task_id: str, task_type: str, description: str):
        """通知任务创建"""
        await self.send_system_notification(
            NotificationType.TASK_CREATED,
            "新任务创建",
            f"任务 ID: {task_id}",
            data={
                "task_id": task_id,
                "task_type": task_type,
                "description": description
            }
        )
    
    async def notify_task_completed(self, task_id: str, task_type: str, result: str):
        """通知任务完成"""
        await self.send_system_notification(
            NotificationType.TASK_COMPLETED,
            "任务完成",
            f"任务 ID: {task_id}",
            data={
                "task_id": task_id,
                "task_type": task_type,
                "result": result
            }
        )
    
    async def notify_error(self, error: str, level: str = "ERROR"):
        """通知错误"""
        await self.send_system_notification(
            NotificationType.ERROR_ALERT,
            "错误警报",
            f"错误：{error}",
            data={
                "error": error,
                "level": level,
                "timestamp": datetime.now().isoformat()
            }
        )
