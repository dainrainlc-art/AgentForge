"""社交媒体集成模块

提供 Twitter、LinkedIn、Facebook、Instagram、YouTube 的 API 集成。
"""

from .twitter_client import TwitterClient, Tweet, TwitterUser
from .linkedin_client import LinkedInClient, LinkedInProfile, LinkedInPost
from .meta_client import MetaClient, FacebookPage, FacebookPost, InstagramMedia
from .youtube_client import YouTubeClient, YouTubeVideo, YouTubePlaylist, YouTubeComment
from .publish_scheduler import (
    PublishScheduler,
    PublishTask,
    PublishStatus,
    Platform
)

__all__ = [
    "TwitterClient",
    "Tweet",
    "TwitterUser",
    "LinkedInClient",
    "LinkedInProfile",
    "LinkedInPost",
    "MetaClient",
    "FacebookPage",
    "FacebookPost",
    "InstagramMedia",
    "YouTubeClient",
    "YouTubeVideo",
    "YouTubePlaylist",
    "YouTubeComment",
    "PublishScheduler",
    "PublishTask",
    "PublishStatus",
    "Platform",
]
