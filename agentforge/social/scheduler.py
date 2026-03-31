"""
Social Media Scheduler - Scheduled post publishing
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from loguru import logger
from enum import Enum
import asyncio
from uuid import uuid4

from agentforge.social.content_adapter import Platform, AdaptedContent


class ScheduleStatus(str, Enum):
    PENDING = "pending"
    SCHEDULED = "scheduled"
    PUBLISHING = "publishing"
    PUBLISHED = "published"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ScheduledPost(BaseModel):
    """Scheduled post model"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    content: str
    platform: Platform
    scheduled_time: datetime
    status: ScheduleStatus = ScheduleStatus.PENDING
    adapted_content: Optional[AdaptedContent] = None
    hashtags: List[str] = Field(default_factory=list)
    media_urls: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    published_at: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ScheduleConfig(BaseModel):
    """Scheduler configuration"""
    check_interval_seconds: int = 60
    max_scheduled_posts: int = 1000
    retry_delay_seconds: int = 300
    enable_auto_retry: bool = True


class PostScheduler:
    """Schedule and manage social media posts"""
    
    def __init__(self, config: Optional[ScheduleConfig] = None):
        self.config = config or ScheduleConfig()
        self._scheduled_posts: Dict[str, ScheduledPost] = {}
        self._running = False
        self._scheduler_task: Optional[asyncio.Task] = None
        self._publish_callbacks: Dict[Platform, callable] = {}
    
    def register_publisher(
        self,
        platform: Platform,
        callback: callable
    ) -> None:
        """Register a publish callback for a platform"""
        self._publish_callbacks[platform] = callback
        logger.info(f"Registered publisher for {platform.value}")
    
    async def start(self) -> None:
        """Start the scheduler"""
        if self._running:
            logger.warning("Scheduler already running")
            return
        
        self._running = True
        self._scheduler_task = asyncio.create_task(self._scheduler_loop())
        logger.info("Post scheduler started")
    
    async def stop(self) -> None:
        """Stop the scheduler"""
        self._running = False
        
        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Post scheduler stopped")
    
    async def _scheduler_loop(self) -> None:
        """Main scheduler loop"""
        while self._running:
            try:
                await self._process_scheduled_posts()
                await asyncio.sleep(self.config.check_interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scheduler loop error: {e}")
                await asyncio.sleep(10)
    
    async def _process_scheduled_posts(self) -> None:
        """Process posts that are due"""
        now = datetime.now()
        
        due_posts = [
            post for post in self._scheduled_posts.values()
            if post.status == ScheduleStatus.SCHEDULED
            and post.scheduled_time <= now
        ]
        
        for post in due_posts:
            await self._publish_post(post)
    
    async def _publish_post(self, post: ScheduledPost) -> bool:
        """Publish a scheduled post"""
        logger.info(f"Publishing post {post.id} to {post.platform.value}")
        
        post.status = ScheduleStatus.PUBLISHING
        
        callback = self._publish_callbacks.get(post.platform)
        
        if not callback:
            logger.error(f"No publisher registered for {post.platform.value}")
            post.status = ScheduleStatus.FAILED
            post.error_message = f"No publisher for {post.platform.value}"
            return False
        
        try:
            result = await callback(
                content=post.content,
                hashtags=post.hashtags,
                media_urls=post.media_urls
            )
            
            if result:
                post.status = ScheduleStatus.PUBLISHED
                post.published_at = datetime.now()
                logger.info(f"Post {post.id} published successfully")
                return True
            else:
                return await self._handle_publish_failure(post, "Publish returned False")
                
        except Exception as e:
            return await self._handle_publish_failure(post, str(e))
    
    async def _handle_publish_failure(
        self,
        post: ScheduledPost,
        error: str
    ) -> bool:
        """Handle publish failure with retry logic"""
        post.error_message = error
        post.retry_count += 1
        
        if self.config.enable_auto_retry and post.retry_count < post.max_retries:
            retry_time = datetime.now() + timedelta(seconds=self.config.retry_delay_seconds)
            post.scheduled_time = retry_time
            post.status = ScheduleStatus.SCHEDULED
            logger.warning(f"Post {post.id} failed, retry {post.retry_count} scheduled for {retry_time}")
            return False
        else:
            post.status = ScheduleStatus.FAILED
            logger.error(f"Post {post.id} failed permanently: {error}")
            return False
    
    def schedule_post(
        self,
        content: str,
        platform: Platform,
        scheduled_time: datetime,
        hashtags: Optional[List[str]] = None,
        media_urls: Optional[List[str]] = None,
        adapted_content: Optional[AdaptedContent] = None
    ) -> ScheduledPost:
        """Schedule a new post"""
        
        if len(self._scheduled_posts) >= self.config.max_scheduled_posts:
            raise ValueError("Maximum scheduled posts limit reached")
        
        post = ScheduledPost(
            content=content,
            platform=platform,
            scheduled_time=scheduled_time,
            hashtags=hashtags or [],
            media_urls=media_urls or [],
            adapted_content=adapted_content,
            status=ScheduleStatus.SCHEDULED
        )
        
        self._scheduled_posts[post.id] = post
        
        logger.info(f"Scheduled post {post.id} for {platform.value} at {scheduled_time}")
        
        return post
    
    def schedule_recurring(
        self,
        content: str,
        platform: Platform,
        start_time: datetime,
        interval: timedelta,
        count: int = 10,
        hashtags: Optional[List[str]] = None
    ) -> List[ScheduledPost]:
        """Schedule recurring posts"""
        
        posts = []
        
        for i in range(count):
            scheduled_time = start_time + (interval * i)
            post = self.schedule_post(
                content=content,
                platform=platform,
                scheduled_time=scheduled_time,
                hashtags=hashtags
            )
            posts.append(post)
        
        logger.info(f"Scheduled {len(posts)} recurring posts for {platform.value}")
        
        return posts
    
    def cancel_post(self, post_id: str) -> bool:
        """Cancel a scheduled post"""
        
        if post_id not in self._scheduled_posts:
            return False
        
        post = self._scheduled_posts[post_id]
        
        if post.status in [ScheduleStatus.PUBLISHED, ScheduleStatus.PUBLISHING]:
            return False
        
        post.status = ScheduleStatus.CANCELLED
        logger.info(f"Cancelled post {post_id}")
        
        return True
    
    def reschedule_post(
        self,
        post_id: str,
        new_time: datetime
    ) -> bool:
        """Reschedule a post"""
        
        if post_id not in self._scheduled_posts:
            return False
        
        post = self._scheduled_posts[post_id]
        
        if post.status != ScheduleStatus.SCHEDULED:
            return False
        
        post.scheduled_time = new_time
        logger.info(f"Rescheduled post {post_id} to {new_time}")
        
        return True
    
    def get_post(self, post_id: str) -> Optional[ScheduledPost]:
        """Get a scheduled post by ID"""
        return self._scheduled_posts.get(post_id)
    
    def get_scheduled_posts(
        self,
        platform: Optional[Platform] = None,
        status: Optional[ScheduleStatus] = None,
        limit: int = 50
    ) -> List[ScheduledPost]:
        """Get scheduled posts with optional filters"""
        
        posts = list(self._scheduled_posts.values())
        
        if platform:
            posts = [p for p in posts if p.platform == platform]
        
        if status:
            posts = [p for p in posts if p.status == status]
        
        posts.sort(key=lambda p: p.scheduled_time)
        
        return posts[:limit]
    
    def get_upcoming_posts(
        self,
        hours: int = 24,
        platform: Optional[Platform] = None
    ) -> List[ScheduledPost]:
        """Get posts scheduled in the next N hours"""
        
        now = datetime.now()
        cutoff = now + timedelta(hours=hours)
        
        posts = [
            p for p in self._scheduled_posts.values()
            if p.status == ScheduleStatus.SCHEDULED
            and now <= p.scheduled_time <= cutoff
        ]
        
        if platform:
            posts = [p for p in posts if p.platform == platform]
        
        posts.sort(key=lambda p: p.scheduled_time)
        
        return posts
    
    def get_scheduler_stats(self) -> Dict[str, Any]:
        """Get scheduler statistics"""
        
        status_counts = {}
        for status in ScheduleStatus:
            status_counts[status.value] = sum(
                1 for p in self._scheduled_posts.values()
                if p.status == status
            )
        
        platform_counts = {}
        for platform in Platform:
            platform_counts[platform.value] = sum(
                1 for p in self._scheduled_posts.values()
                if p.platform == platform and p.status == ScheduleStatus.SCHEDULED
            )
        
        return {
            "total_posts": len(self._scheduled_posts),
            "status_breakdown": status_counts,
            "platform_breakdown": platform_counts,
            "running": self._running,
            "next_post": min(
                (p.scheduled_time for p in self._scheduled_posts.values()
                 if p.status == ScheduleStatus.SCHEDULED),
                default=None
            )
        }
    
    def suggest_best_times(
        self,
        platform: Platform,
        timezone_offset: int = 0
    ) -> List[datetime]:
        """Suggest best posting times based on platform"""
        
        best_hours = {
            Platform.TWITTER: [9, 12, 17, 18],
            Platform.LINKEDIN: [7, 8, 12, 17, 18],
            Platform.INSTAGRAM: [11, 13, 19, 21],
            Platform.FACEBOOK: [9, 13, 16, 19],
            Platform.YOUTUBE: [14, 15, 16, 20],
            Platform.TIKTOK: [19, 20, 21, 22],
        }
        
        hours = best_hours.get(platform, [9, 12, 17])
        
        now = datetime.now()
        suggestions = []
        
        for day_offset in range(7):
            for hour in hours:
                suggested = now.replace(
                    hour=hour,
                    minute=0,
                    second=0,
                    microsecond=0
                ) + timedelta(days=day_offset)
                
                if suggested > now:
                    suggestions.append(suggested)
        
        return suggestions[:10]


post_scheduler = PostScheduler()
