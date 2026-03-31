"""
AgentForge LinkedIn Integration Models
LinkedIn 数据模型定义
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, EmailStr


class Visibility(str, Enum):
    """可见性枚举"""
    PUBLIC = "public"
    PRIVATE = "private"
    CONNECTIONS_ONLY = "connections_only"


class Industry(str, Enum):
    """行业枚举"""
    TECHNOLOGY = "technology"
    FINANCE = "finance"
    HEALTHCARE = "healthcare"
    EDUCATION = "education"
    MARKETING = "marketing"
    CONSULTING = "consulting"
    OTHER = "other"


class Profile(BaseModel):
    """个人资料模型"""
    id: str
    first_name: str
    last_name: str
    full_name: str
    headline: str = ""  # 标题/座右铭
    summary: str = ""  # 个人简介
    location: str = ""  # 地理位置
    country: str = ""  # 国家
    industry: Optional[Industry] = None  # 行业
    profile_picture_url: Optional[str] = None  # 头像 URL
    background_cover_image_url: Optional[str] = None  # 背景图 URL
    public_profile_url: str  # 公开主页 URL
    follower_count: int = 0  # 粉丝数
    connection_count: int = 0  # 人脉数
    
    # 工作经历
    experiences: List[Dict[str, Any]] = Field(default_factory=list)
    
    # 教育经历
    educations: List[Dict[str, Any]] = Field(default_factory=list)
    
    # 技能
    skills: List[str] = Field(default_factory=list)
    
    # 认证
    certifications: List[Dict[str, Any]] = Field(default_factory=list)
    
    # 语言
    languages: List[str] = Field(default_factory=list)
    
    # 联系方式
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    twitter: Optional[str] = None
    websites: List[str] = Field(default_factory=list)
    
    # 元数据
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class Connection(BaseModel):
    """人脉模型"""
    id: str
    first_name: str
    last_name: str
    full_name: str
    headline: str = ""  # 头衔
    location: str = ""  # 位置
    profile_picture_url: Optional[str] = None
    public_profile_url: str
    
    # 关系信息
    connection_degree: str = "1st"  # 1st, 2nd, 3rd
    connected_at: Optional[datetime] = None
    
    # 工作信息
    current_company: str = ""
    current_position: str = ""
    
    # 共同人脉
    mutual_connections_count: int = 0
    
    # 元数据
    created_at: datetime = Field(default_factory=datetime.now)


class Message(BaseModel):
    """消息模型"""
    id: str
    conversation_id: str
    sender_id: str
    receiver_id: str
    text: str
    created_at: datetime = Field(default_factory=datetime.now)
    read: bool = False
    
    # 附件
    attachments: List[Dict[str, Any]] = Field(default_factory=list)


class Post(BaseModel):
    """动态/帖子模型"""
    id: str
    author_id: str
    text: str
    visibility: Visibility = Visibility.PUBLIC
    
    # 媒体
    images: List[str] = Field(default_factory=list)
    video_url: Optional[str] = None
    article_url: Optional[str] = None
    
    # 互动数据
    like_count: int = 0
    comment_count: int = 0
    share_count: int = 0
    impression_count: int = 0
    
    # 元数据
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    # 标签
    hashtags: List[str] = Field(default_factory=list)
    
    # 提及
    mentions: List[str] = Field(default_factory=list)


class Job(BaseModel):
    """职位模型"""
    id: str
    title: str
    company: str
    company_id: str
    company_logo_url: Optional[str] = None
    location: str
    description: str
    employment_type: str = "full_time"  # full_time, part_time, contract, internship
    seniority_level: str = "mid_senior"  # intern, entry, associate, mid_senior, director, executive
    industries: List[str] = Field(default_factory=list)
    
    # 薪资范围
    salary_range_min: Optional[int] = None
    salary_range_max: Optional[int] = None
    salary_currency: str = "USD"
    salary_period: str = "yearly"  # yearly, monthly, hourly
    
    # 技能要求
    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    
    # 申请信息
    applicant_count: int = 0
    apply_url: Optional[str] = None
    
    # 元数据
    posted_at: datetime = Field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None


class Comment(BaseModel):
    """评论模型"""
    id: str
    post_id: str
    author_id: str
    text: str
    created_at: datetime = Field(default_factory=datetime.now)
    
    # 互动
    like_count: int = 0
    reply_count: int = 0


class Company(BaseModel):
    """公司模型"""
    id: str
    name: str
    universal_name: str
    logo_url: Optional[str] = None
    cover_image_url: Optional[str] = None
    description: str = ""
    website: str = ""
    industry: str = ""
    company_size: str = ""  # 1-10, 11-50, 51-200, etc.
    company_type: str = ""  # public, private, nonprofit, etc.
    founded_year: Optional[int] = None
    specialties: List[str] = Field(default_factory=list)
    
    # 地址
    street: str = ""
    city: str = ""
    state: str = ""
    postal_code: str = ""
    country: str = ""
    
    # 社交媒体
    follower_count: int = 0
    employee_count: int = 0
    
    # 元数据
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class Share(BaseModel):
    """分享模型"""
    id: str
    post_id: str
    user_id: str
    text: str = ""  # 分享时的评论
    created_at: datetime = Field(default_factory=datetime.now)


class Notification(BaseModel):
    """通知模型"""
    id: str
    type: str  # connection_request, message, comment, like, share, mention, job_posting
    actor_id: str
    actor_name: str
    actor_profile_url: str
    content: str
    read: bool = False
    created_at: datetime = Field(default_factory=datetime.now)
    
    # 关联对象
    related_post_id: Optional[str] = None
    related_message_id: Optional[str] = None
    related_job_id: Optional[str] = None


class Analytics(BaseModel):
    """分析数据模型"""
    profile_views: int = 0  # 个人主页浏览量
    post_impressions: int = 0  # 帖子曝光量
    search_appearances: int = 0  # 搜索出现次数
    connection_requests: int = 0  # 人脉请求数
    
    # 时间段
    period: str = "last_7_days"  # last_7_days, last_30_days, last_90_days
    
    # 元数据
    updated_at: datetime = Field(default_factory=datetime.now)


class LinkedInError(BaseModel):
    """LinkedIn API 错误模型"""
    status: int
    message: str
    code: str
    documentation_url: Optional[str] = None
    request_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class PaginationParams(BaseModel):
    """分页参数"""
    start: int = 0
    count: int = 10
    q: Optional[str] = None  # 查询条件
    sort: Optional[str] = None  # 排序字段
