"""
AgentForge Telegram Bot Integration Models
Telegram Bot 数据模型定义
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class MessageType(str, Enum):
    """消息类型"""
    TEXT = "text"
    PHOTO = "photo"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"
    STICKER = "sticker"
    LOCATION = "location"
    CONTACT = "contact"


class ChatType(str, Enum):
    """聊天类型"""
    PRIVATE = "private"
    GROUP = "group"
    SUPERGROUP = "supergroup"
    CHANNEL = "channel"


class User(BaseModel):
    """Telegram 用户模型"""
    id: int
    is_bot: bool = False
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    language_code: Optional[str] = None
    is_premium: bool = False
    
    # 元数据
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class Chat(BaseModel):
    """Telegram 聊天模型"""
    id: int
    type: ChatType
    title: Optional[str] = None
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    
    # 群组成品
    member_count: int = 0
    description: Optional[str] = None
    
    # 元数据
    created_at: datetime = Field(default_factory=datetime.now)


class Message(BaseModel):
    """Telegram 消息模型"""
    message_id: int
    chat: Chat
    from_user: Optional[User] = None
    date: datetime
    text: Optional[str] = None
    message_type: MessageType = MessageType.TEXT
    
    # 媒体内容
    photo: Optional[List[Dict[str, Any]]] = None
    video: Optional[Dict[str, Any]] = None
    audio: Optional[Dict[str, Any]] = None
    document: Optional[Dict[str, Any]] = None
    sticker: Optional[Dict[str, Any]] = None
    
    # 位置
    location: Optional[Dict[str, Any]] = None
    contact: Optional[Dict[str, Any]] = None
    
    # 回复
    reply_to_message: Optional["Message"] = None
    
    # 元数据
    created_at: datetime = Field(default_factory=datetime.now)


class CallbackQuery(BaseModel):
    """回调查询模型"""
    id: str
    from_user: User
    message: Optional[Message] = None
    chat_instance: str
    data: str  # 回调数据


class InlineQuery(BaseModel):
    """内联查询模型"""
    id: str
    from_user: User
    query: str  # 查询文本
    offset: str
    chat_type: Optional[str] = None
    location: Optional[Dict[str, Any]] = None


class BotCommand(BaseModel):
    """机器人命令模型"""
    command: str
    description: str


class NotificationType(str, Enum):
    """通知类型"""
    SYSTEM_STATUS = "system_status"
    TASK_CREATED = "task_created"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    ERROR_ALERT = "error_alert"
    SELF_EVOLUTION = "self_evolution"
    CUSTOM = "custom"


class Notification(BaseModel):
    """通知模型"""
    id: str
    type: NotificationType
    title: str
    message: str
    chat_id: int
    user_id: Optional[int] = None
    
    # 附加数据
    data: Optional[Dict[str, Any]] = None
    
    # 状态
    sent: bool = False
    sent_at: Optional[datetime] = None
    
    # 元数据
    created_at: datetime = Field(default_factory=datetime.now)


class NotificationTemplate(BaseModel):
    """通知模板模型"""
    type: NotificationType
    title_template: str
    message_template: str
    parse_mode: str = "HTML"  # HTML or Markdown


class Subscriber(BaseModel):
    """订阅者模型"""
    user_id: int
    chat_id: int
    username: Optional[str] = None
    first_name: str
    last_name: Optional[str] = None
    
    # 订阅偏好
    subscribed_types: List[NotificationType] = Field(default_factory=list)
    enabled: bool = True
    
    # 元数据
    subscribed_at: datetime = Field(default_factory=datetime.now)
    last_notification_at: Optional[datetime] = None


class CommandHandler(BaseModel):
    """命令处理器模型"""
    command: str
    description: str
    handler_name: str
    requires_auth: bool = False
    allowed_chat_types: List[ChatType] = Field(default_factory=list)


class WebhookInfo(BaseModel):
    """Webhook 信息模型"""
    url: str
    has_custom_certificate: bool = False
    pending_update_count: int = 0
    ip_address: Optional[str] = None
    last_error_date: Optional[datetime] = None
    last_error_message: Optional[str] = None
    max_connections: int = 40
    allowed_updates: List[str] = Field(default_factory=list)


class BotInfo(BaseModel):
    """机器人信息模型"""
    id: int
    is_bot: bool = True
    first_name: str
    username: str
    can_join_groups: bool = False
    can_read_all_group_messages: bool = False
    supports_inline_queries: bool = False


class Update(BaseModel):
    """更新模型"""
    update_id: int
    message: Optional[Message] = None
    edited_message: Optional[Message] = None
    channel_post: Optional[Message] = None
    edited_channel_post: Optional[Message] = None
    callback_query: Optional[CallbackQuery] = None
    callback_query_id: Optional[str] = None
    inline_query: Optional[InlineQuery] = None
    chosen_inline_result: Optional[Dict[str, Any]] = None


class SendMessageRequest(BaseModel):
    """发送消息请求"""
    chat_id: int
    text: str
    parse_mode: Optional[str] = None  # HTML, Markdown, MarkdownV2
    disable_web_page_preview: bool = False
    disable_notification: bool = False
    reply_to_message_id: Optional[int] = None


class SendPhotoRequest(BaseModel):
    """发送照片请求"""
    chat_id: int
    photo: str  # URL or file_id
    caption: Optional[str] = None
    parse_mode: Optional[str] = None
    disable_notification: bool = False
    reply_to_message_id: Optional[int] = None


class SendDocumentRequest(BaseModel):
    """发送文档请求"""
    chat_id: int
    document: str  # URL or file_id
    caption: Optional[str] = None
    parse_mode: Optional[str] = None
    disable_notification: bool = False
    reply_to_message_id: Optional[int] = None


class EditMessageTextRequest(BaseModel):
    """编辑消息请求"""
    chat_id: Optional[int] = None
    message_id: Optional[int] = None
    inline_message_id: Optional[str] = None
    text: str
    parse_mode: Optional[str] = None
    disable_web_page_preview: bool = False


class TelegramError(BaseModel):
    """Telegram API 错误模型"""
    ok: bool = False
    error_code: int
    description: str
    parameters: Optional[Dict[str, Any]] = None


class TelegramResponse(BaseModel):
    """Telegram API 响应模型"""
    ok: bool
    result: Optional[Any] = None
    error_code: Optional[int] = None
    description: Optional[str] = None


# 预定义的通知模板
DEFAULT_NOTIFICATION_TEMPLATES = {
    NotificationType.SYSTEM_STATUS: NotificationTemplate(
        type=NotificationType.SYSTEM_STATUS,
        title_template="🤖 系统状态",
        message_template="<b>服务</b>: {service}\n<b>状态</b>: {status}\n<b>时间</b>: {timestamp}",
        parse_mode="HTML"
    ),
    NotificationType.TASK_CREATED: NotificationTemplate(
        type=NotificationType.TASK_CREATED,
        title_template="📋 新任务创建",
        message_template="<b>任务 ID</b>: {task_id}\n<b>类型</b>: {task_type}\n<b>描述</b>: {description}",
        parse_mode="HTML"
    ),
    NotificationType.TASK_COMPLETED: NotificationTemplate(
        type=NotificationType.TASK_COMPLETED,
        title_template="✅ 任务完成",
        message_template="<b>任务 ID</b>: {task_id}\n<b>类型</b>: {task_type}\n<b>结果</b>: {result}",
        parse_mode="HTML"
    ),
    NotificationType.TASK_FAILED: NotificationTemplate(
        type=NotificationType.TASK_FAILED,
        title_template="❌ 任务失败",
        message_template="<b>任务 ID</b>: {task_id}\n<b>类型</b>: {task_type}\n<b>错误</b>: {error}",
        parse_mode="HTML"
    ),
    NotificationType.ERROR_ALERT: NotificationTemplate(
        type=NotificationType.ERROR_ALERT,
        title_template="⚠️ 错误警报",
        message_template="<b>错误</b>: {error}\n<b>级别</b>: {level}\n<b>时间</b>: {timestamp}",
        parse_mode="HTML"
    ),
    NotificationType.SELF_EVOLUTION: NotificationTemplate(
        type=NotificationType.SELF_EVOLUTION,
        title_template="🔄 自进化系统",
        message_template="<b>任务</b>: {task_type}\n<b>状态</b>: {status}\n<b>详情</b>: {details}",
        parse_mode="HTML"
    )
}
