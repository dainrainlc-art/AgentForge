"""社交媒体统一发布调度器

功能特性:
- 多平台发布队列
- 速率控制
- 失败重试
- 发布日历
- 最佳发布时间推荐
"""

import os
import json
import asyncio
import logging
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
import heapq

from .twitter_client import TwitterClient
from .linkedin_client import LinkedInClient
from .meta_client import MetaClient
from .youtube_client import YouTubeClient

logger = logging.getLogger(__name__)


class Platform(Enum):
    """平台类型"""
    TWITTER = "twitter"
    LINKEDIN = "linkedin"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    YOUTUBE = "youtube"


class PublishStatus(Enum):
    """发布状态"""
    PENDING = "pending"
    SCHEDULED = "scheduled"
    PUBLISHING = "publishing"
    PUBLISHED = "published"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class PublishTask:
    """发布任务"""
    id: str
    platform: Platform
    content: str
    media_urls: List[str] = field(default_factory=list)
    scheduled_time: Optional[datetime] = None
    status: PublishStatus = PublishStatus.PENDING
    result_id: Optional[str] = None
    result_url: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    def __lt__(self, other):
        if self.scheduled_time and other.scheduled_time:
            return self.scheduled_time < other.scheduled_time
        return self.created_at < other.created_at

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "platform": self.platform.value,
            "content": self.content,
            "media_urls": self.media_urls,
            "scheduled_time": self.scheduled_time.isoformat() if self.scheduled_time else None,
            "status": self.status.value,
            "result_id": self.result_id,
            "result_url": self.result_url,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class PlatformConfig:
    """平台配置"""
    platform: Platform
    enabled: bool = True
    rate_limit_per_hour: int = 10
    rate_limit_per_day: int = 50
    best_times: List[int] = field(default_factory=lambda: [9, 12, 17, 20])


class PublishScheduler:
    """统一发布调度器"""

    DEFAULT_BEST_TIMES = {
        Platform.TWITTER: [9, 12, 17, 20],
        Platform.LINKEDIN: [8, 12, 17, 18],
        Platform.FACEBOOK: [9, 13, 16, 19],
        Platform.INSTAGRAM: [11, 14, 19, 21],
        Platform.YOUTUBE: [15, 16, 17, 18]
    }

    def __init__(self, state_path: str = "./data/publish_queue.json"):
        self.state_path = Path(state_path)

        self._clients: Dict[Platform, Any] = {}
        self._queue: List[PublishTask] = []
        self._rate_limits: Dict[Platform, List[datetime]] = {}
        self._configs: Dict[Platform, PlatformConfig] = {}
        self._running = False

        self._initialize_configs()
        self._load_state()

    def _initialize_configs(self):
        for platform in Platform:
            self._configs[platform] = PlatformConfig(
                platform=platform,
                best_times=self.DEFAULT_BEST_TIMES.get(platform, [9, 12, 17, 20])
            )
            self._rate_limits[platform] = []

    def _load_state(self):
        if self.state_path.exists():
            try:
                with open(self.state_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for task_data in data.get("tasks", []):
                        task = PublishTask(
                            id=task_data["id"],
                            platform=Platform(task_data["platform"]),
                            content=task_data["content"],
                            media_urls=task_data.get("media_urls", []),
                            scheduled_time=self._parse_datetime(task_data.get("scheduled_time")),
                            status=PublishStatus(task_data.get("status", "pending")),
                            result_id=task_data.get("result_id"),
                            result_url=task_data.get("result_url"),
                            error_message=task_data.get("error_message"),
                            retry_count=task_data.get("retry_count", 0),
                            max_retries=task_data.get("max_retries", 3),
                            metadata=task_data.get("metadata", {}),
                            created_at=self._parse_datetime(task_data.get("created_at")) or datetime.now()
                        )
                        if task.status in [PublishStatus.PENDING, PublishStatus.SCHEDULED]:
                            heapq.heappush(self._queue, task)
                logger.info(f"加载 {len(self._queue)} 个待发布任务")
            except Exception as e:
                logger.warning(f"加载发布队列状态失败: {e}")

    def _save_state(self):
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "tasks": [t.to_dict() for t in self._queue],
            "last_updated": datetime.now().isoformat()
        }
        with open(self.state_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _parse_datetime(self, dt_str: Optional[str]) -> Optional[datetime]:
        if not dt_str:
            return None
        try:
            return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        except:
            return None

    def set_client(self, platform: Platform, client: Any):
        self._clients[platform] = client

    async def _get_client(self, platform: Platform) -> Any:
        if platform not in self._clients:
            if platform == Platform.TWITTER:
                self._clients[platform] = TwitterClient()
            elif platform == Platform.LINKEDIN:
                self._clients[platform] = LinkedInClient()
            elif platform in [Platform.FACEBOOK, Platform.INSTAGRAM]:
                self._clients[platform] = MetaClient()
            elif platform == Platform.YOUTUBE:
                self._clients[platform] = YouTubeClient()

        return self._clients.get(platform)

    def add_task(
        self,
        platform: Platform,
        content: str,
        media_urls: Optional[List[str]] = None,
        scheduled_time: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> PublishTask:
        import secrets

        task = PublishTask(
            id=f"pub_{secrets.token_urlsafe(8)}",
            platform=platform,
            content=content,
            media_urls=media_urls or [],
            scheduled_time=scheduled_time,
            metadata=metadata or {}
        )

        if scheduled_time:
            task.status = PublishStatus.SCHEDULED
        else:
            task.status = PublishStatus.PENDING

        heapq.heappush(self._queue, task)
        self._save_state()

        logger.info(f"添加发布任务: {task.id} -> {platform.value}")
        return task

    def add_multi_platform_task(
        self,
        platforms: List[Platform],
        content: str,
        media_urls: Optional[List[str]] = None,
        scheduled_time: Optional[datetime] = None
    ) -> List[PublishTask]:
        tasks = []
        for platform in platforms:
            task = self.add_task(platform, content, media_urls, scheduled_time)
            tasks.append(task)
        return tasks

    def suggest_best_time(self, platform: Platform) -> datetime:
        config = self._configs.get(platform)
        if not config:
            return datetime.now() + timedelta(hours=1)

        now = datetime.now()
        best_hours = config.best_times

        for hour in sorted(best_hours):
            suggested = now.replace(hour=hour, minute=0, second=0, microsecond=0)
            if suggested > now:
                return suggested

        tomorrow = now + timedelta(days=1)
        return tomorrow.replace(hour=best_hours[0], minute=0, second=0, microsecond=0)

    def _check_rate_limit(self, platform: Platform) -> bool:
        config = self._configs.get(platform)
        if not config:
            return True

        now = datetime.now()
        hour_ago = now - timedelta(hours=1)
        day_ago = now - timedelta(days=1)

        hour_requests = sum(1 for t in self._rate_limits[platform] if t > hour_ago)
        day_requests = sum(1 for t in self._rate_limits[platform] if t > day_ago)

        if hour_requests >= config.rate_limit_per_hour:
            return False
        if day_requests >= config.rate_limit_per_day:
            return False

        return True

    async def _publish_task(self, task: PublishTask) -> PublishTask:
        client = await self._get_client(task.platform)

        if not client:
            task.status = PublishStatus.FAILED
            task.error_message = f"未配置 {task.platform.value} 客户端"
            return task

        if not self._check_rate_limit(task.platform):
            task.scheduled_time = datetime.now() + timedelta(minutes=30)
            task.status = PublishStatus.SCHEDULED
            return task

        task.status = PublishTask.PUBLISHING

        try:
            if task.platform == Platform.TWITTER:
                if len(task.media_urls) > 0:
                    result = await client.post_tweet(task.content, media_ids=task.media_urls)
                else:
                    result = await client.post_tweet(task.content)
                task.result_id = result.id
                task.result_url = f"https://twitter.com/user/status/{result.id}"

            elif task.platform == Platform.LINKEDIN:
                if len(task.media_urls) > 0:
                    result = await client.post_text(task.content)
                else:
                    result = await client.post_text(task.content)
                task.result_id = result.id

            elif task.platform == Platform.FACEBOOK:
                if len(task.media_urls) > 0:
                    result = await client.post_to_page(task.content, media_url=task.media_urls[0])
                else:
                    result = await client.post_to_page(task.content)
                task.result_id = result.id

            elif task.platform == Platform.INSTAGRAM:
                if len(task.media_urls) > 0:
                    result = await client.post_to_instagram(task.media_urls[0], task.content)
                    task.result_id = result.id

            elif task.platform == Platform.YOUTUBE:
                pass

            task.status = PublishStatus.PUBLISHED
            self._rate_limits[task.platform].append(datetime.now())
            logger.info(f"发布成功: {task.id} -> {task.platform.value}")

        except Exception as e:
            task.retry_count += 1
            task.error_message = str(e)

            if task.retry_count >= task.max_retries:
                task.status = PublishStatus.FAILED
                logger.error(f"发布失败 (已达最大重试次数): {task.id} - {e}")
            else:
                task.status = PublishStatus.SCHEDULED
                task.scheduled_time = datetime.now() + timedelta(minutes=15 * task.retry_count)
                logger.warning(f"发布失败，将重试: {task.id} - {e}")

        return task

    async def process_queue(self) -> List[PublishTask]:
        processed = []
        now = datetime.now()

        ready_tasks = []
        while self._queue:
            task = heapq.heappop(self._queue)
            if task.status in [PublishStatus.PENDING, PublishStatus.SCHEDULED]:
                if not task.scheduled_time or task.scheduled_time <= now:
                    ready_tasks.append(task)
                else:
                    heapq.heappush(self._queue, task)
                    break

        for task in ready_tasks:
            result = await self._publish_task(task)
            processed.append(result)

            if result.status == PublishStatus.SCHEDULED:
                heapq.heappush(self._queue, result)

        self._save_state()
        return processed

    async def start(self):
        self._running = True
        logger.info("发布调度器启动")

        while self._running:
            try:
                await self.process_queue()
                await asyncio.sleep(60)
            except Exception as e:
                logger.error(f"调度器错误: {e}")
                await asyncio.sleep(60)

    def stop(self):
        self._running = False
        logger.info("发布调度器停止")

    def get_pending_tasks(self) -> List[PublishTask]:
        return sorted(self._queue)

    def cancel_task(self, task_id: str) -> bool:
        for i, task in enumerate(self._queue):
            if task.id == task_id:
                task.status = PublishStatus.CANCELLED
                self._queue.pop(i)
                heapq.heapify(self._queue)
                self._save_state()
                return True
        return False

    def get_calendar(self, days: int = 7) -> Dict[str, List[Dict[str, Any]]]:
        calendar: Dict[str, List[Dict[str, Any]]] = {}

        for task in self._queue:
            if task.scheduled_time:
                date_key = task.scheduled_time.strftime("%Y-%m-%d")
                if date_key not in calendar:
                    calendar[date_key] = []
                calendar[date_key].append(task.to_dict())

        return calendar

    def get_stats(self) -> Dict[str, Any]:
        status_counts = {}
        for status in PublishStatus:
            status_counts[status.value] = sum(
                1 for t in self._queue if t.status == status
            )

        platform_counts = {}
        for platform in Platform:
            platform_counts[platform.value] = sum(
                1 for t in self._queue if t.platform == platform
            )

        return {
            "total_tasks": len(self._queue),
            "by_status": status_counts,
            "by_platform": platform_counts
        }
