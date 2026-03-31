"""
AgentForge Feishu (Lark) Integration Models
飞书数据模型定义
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, EmailStr


class MessageType(str, Enum):
    """消息类型"""
    TEXT = "text"
    POST = "post"  # 富文本
    IMAGE = "image"
    FILE = "file"
    AUDIO = "audio"
    MEDIA = "media"
    STICKER = "sticker"
    INTERACTIVE = "interactive"  # 交互式卡片


class ChatType(str, Enum):
    """聊天类型"""
    PRIVATE = "private"
    GROUP = "group"


class User(BaseModel):
    """飞书用户模型"""
    user_id: str
    open_id: str
    union_id: str
    name: str
    en_name: Optional[str] = None
    nickname: Optional[str] = None
    email: Optional[EmailStr] = None
    mobile: Optional[str] = None
    gender: int = 0  # 0-未知，1-男，2-女
    avatar: Optional[str] = None
    avatar_thumb: Optional[str] = None
    avatar_middle: Optional[str] = None
    avatar_large: Optional[str] = None
    status: int = 0  # 0-未激活，1-已激活，2-已冻结，3-已离职
    department_ids: List[str] = Field(default_factory=list)
    job_number: Optional[str] = None
    employee_type: int = 0
    employee_no: Optional[str] = None
    employee_rank: Optional[str] = None
    work_station: Optional[str] = None
    
    # 元数据
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class Chat(BaseModel):
    """飞书群聊模型"""
    chat_id: str
    name: str
    description: str = ""
    owner_id: str
    user_ids: List[str] = Field(default_factory=list)
    external: bool = False
    join_approval: bool = False
    invite_approval: bool = False
    chat_mode: str = "group"  # group, live
    message_setting: int = 0
    
    # 元数据
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class Message(BaseModel):
    """飞书消息模型"""
    message_id: str
    chat_id: str
    sender_id: str
    sender_type: str = "user"  # user, bot
    content: str
    message_type: MessageType = MessageType.TEXT
    create_time: datetime
    update_time: Optional[datetime] = None
    
    # 元数据
    created_at: datetime = Field(default_factory=datetime.now)


class RichTextContent(BaseModel):
    """富文本内容"""
    tag: str = "text"  # text, a, b, i, u, s, img
    text: Optional[str] = None
    href: Optional[str] = None
    image_key: Optional[str] = None
    style: Optional[Dict[str, Any]] = None


class InteractiveCard(BaseModel):
    """交互式卡片"""
    config: Dict[str, Any] = Field(default_factory=lambda: {"wide_screen_mode": True})
    header: Optional[Dict[str, Any]] = None
    elements: List[Dict[str, Any]] = Field(default_factory=list)


class CalendarEvent(BaseModel):
    """日历事件模型"""
    event_id: str
    summary: str
    description: str = ""
    start_time: datetime
    end_time: datetime
    timezone: str = "Asia/Shanghai"
    location: str = ""
    organizer_id: str
    attendee_ids: List[str] = Field(default_factory=list)
    status: str = "confirmed"  # confirmed, cancelled
    reminders: List[int] = Field(default_factory=list)  # 提醒时间（分钟）
    
    # 元数据
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class Document(BaseModel):
    """云文档模型"""
    doc_id: str
    title: str
    doc_type: str = "doc"  # doc, sheet, slide, folder
    owner_id: str
    create_time: datetime
    update_time: datetime
    edit_time: Optional[datetime] = None
    url: str
    parent_folder_id: Optional[str] = None
    
    # 元数据
    created_at: datetime = Field(default_factory=datetime.now)


class NotificationType(str, Enum):
    """通知类型"""
    SYSTEM_STATUS = "system_status"
    TASK_CREATED = "task_created"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    ERROR_ALERT = "error_alert"
    MEETING_REMINDER = "meeting_reminder"
    DOCUMENT_UPDATE = "document_update"
    CUSTOM = "custom"


class Notification(BaseModel):
    """通知模型"""
    id: str
    type: NotificationType
    title: str
    content: str
    receiver_id: str
    receiver_type: str = "user"  # user, chat
    message_type: MessageType = MessageType.TEXT
    
    # 附加数据
    data: Optional[Dict[str, Any]] = None
    
    # 状态
    sent: bool = False
    sent_at: Optional[datetime] = None
    
    # 元数据
    created_at: datetime = Field(default_factory=datetime.now)


class Subscriber(BaseModel):
    """订阅者模型"""
    user_id: str
    open_id: str
    name: str
    email: Optional[EmailStr] = None
    
    # 订阅偏好
    subscribed_types: List[NotificationType] = Field(default_factory=list)
    enabled: bool = True
    
    # 元数据
    subscribed_at: datetime = Field(default_factory=datetime.now)
    last_notification_at: Optional[datetime] = None


class FeishuError(BaseModel):
    """飞书 API 错误模型"""
    code: int
    msg: str
    detail: Optional[Dict[str, Any]] = None


class FeishuResponse(BaseModel):
    """飞书 API 响应模型"""
    code: int = 0
    msg: str = "success"
    data: Optional[Dict[str, Any]] = None


# 预定义的通知模板
DEFAULT_NOTIFICATION_TEMPLATES = {
    NotificationType.SYSTEM_STATUS: {
        "title": "🤖 系统状态",
        "content": "**服务**: {service}\n**状态**: {status}\n**时间**: {timestamp}"
    },
    NotificationType.TASK_CREATED: {
        "title": "📋 新任务创建",
        "content": "**任务 ID**: {task_id}\n**类型**: {task_type}\n**描述**: {description}"
    },
    NotificationType.TASK_COMPLETED: {
        "title": "✅ 任务完成",
        "content": "**任务 ID**: {task_id}\n**类型**: {task_type}\n**结果**: {result}"
    },
    NotificationType.TASK_FAILED: {
        "title": "❌ 任务失败",
        "content": "**任务 ID**: {task_id}\n**类型**: {task_type}\n**错误**: {error}"
    },
    NotificationType.ERROR_ALERT: {
        "title": "⚠️ 错误警报",
        "content": "**错误**: {error}\n**级别**: {level}\n**时间**: {timestamp}"
    },
    NotificationType.MEETING_REMINDER: {
        "title": "📅 会议提醒",
        "content": "**会议主题**: {meeting_title}\n**开始时间**: {start_time}\n**地点**: {location}"
    },
    NotificationType.DOCUMENT_UPDATE: {
        "title": "📄 文档更新",
        "content": "**文档标题**: {doc_title}\n**更新时间**: {update_time}\n**更新人**: {updater}"
    }
}
