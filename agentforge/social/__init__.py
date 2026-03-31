"""
AgentForge Social Media Module
"""
from agentforge.social.content_adapter import (
    ContentAdapter,
    AdaptedContent,
    Platform,
    ContentType,
    PlatformLimits,
    content_adapter
)
from agentforge.social.scheduler import (
    PostScheduler,
    ScheduledPost,
    ScheduleStatus,
    ScheduleConfig,
    post_scheduler
)
from agentforge.social.analytics import (
    SocialAnalytics,
    PostMetrics,
    PlatformAnalytics,
    AnalyticsPeriod,
    social_analytics
)
from agentforge.social.calendar import (
    ContentCalendar,
    CalendarEvent,
    ContentTheme,
    CalendarEventType,
    ContentStatus,
    content_calendar
)
from agentforge.social.account_manager import (
    AccountManager,
    SocialAccount,
    AccountStatus,
    AccountType,
    AccountStats,
    account_manager
)

__all__ = [
    "ContentAdapter",
    "AdaptedContent",
    "Platform",
    "ContentType",
    "PlatformLimits",
    "content_adapter",
    "PostScheduler",
    "ScheduledPost",
    "ScheduleStatus",
    "ScheduleConfig",
    "post_scheduler",
    "SocialAnalytics",
    "PostMetrics",
    "PlatformAnalytics",
    "AnalyticsPeriod",
    "social_analytics",
    "ContentCalendar",
    "CalendarEvent",
    "ContentTheme",
    "CalendarEventType",
    "ContentStatus",
    "content_calendar",
    "AccountManager",
    "SocialAccount",
    "AccountStatus",
    "AccountType",
    "AccountStats",
    "account_manager",
]
