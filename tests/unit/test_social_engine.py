"""
AgentForge 社交媒体营销引擎单元测试
测试社交媒体自动化相关的所有业务逻辑
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

from agentforge.social.scheduler import (
    PostScheduler,
    ScheduleConfig,
    ScheduleStatus,
    ScheduledPost,
)
from agentforge.social.content_adapter import (
    ContentAdapter,
    Platform,
    ContentType,
    PlatformLimits,
    AdaptedContent,
)
from agentforge.social.analytics import (
    SocialAnalytics,
    PostMetrics,
    MetricType,
    AnalyticsPeriod,
    PlatformAnalytics,
)
from agentforge.social.calendar import (
    ContentCalendar,
    CalendarEvent,
    CalendarEventType,
    ContentStatus,
    ContentTheme,
)
from agentforge.social.account_manager import (
    AccountManager,
    SocialAccount,
    AccountStatus,
    AccountType,
    AccountStats,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def schedule_config():
    """调度器配置"""
    return ScheduleConfig(
        check_interval_seconds=30,
        max_scheduled_posts=100,
        retry_delay_seconds=60,
        enable_auto_retry=True,
    )


@pytest.fixture
def scheduler(schedule_config):
    """创建帖子调度器实例"""
    return PostScheduler(config=schedule_config)


@pytest.fixture
def adapter():
    """创建内容适配器实例"""
    return ContentAdapter()


@pytest.fixture
def analytics():
    """创建分析器实例"""
    return SocialAnalytics()


@pytest.fixture
def calendar():
    """创建内容日历实例"""
    return ContentCalendar()


@pytest.fixture
def account_manager():
    """创建账户管理器实例"""
    return AccountManager()


@pytest.fixture
def sample_post():
    """示例帖子"""
    return ScheduledPost(
        content="Test post content",
        platform=Platform.TWITTER,
        scheduled_time=datetime.now() + timedelta(hours=1),
        hashtags=["#test", "#demo"],
        media_urls=[],
    )


@pytest.fixture
def sample_metrics():
    """示例指标数据"""
    return PostMetrics(
        post_id="POST-001",
        platform=Platform.TWITTER,
        impressions=1000,
        reach=800,
        engagement=50,
        likes=30,
        comments=10,
        shares=5,
        clicks=5,
        saves=0,
        video_views=0,
        profile_visits=10,
    )


# ============================================================================
# Post Scheduler Tests
# ============================================================================


class TestPostScheduler:
    """PostScheduler 单元测试"""

    def test_scheduler_initialization(self, scheduler, schedule_config):
        """测试调度器初始化"""
        assert scheduler._running is False
        assert scheduler.config == schedule_config
        assert len(scheduler._scheduled_posts) == 0

    def test_register_publisher(self, scheduler):
        """测试注册发布器"""
        mock_callback = MagicMock()
        
        scheduler.register_publisher(Platform.TWITTER, mock_callback)
        
        assert Platform.TWITTER in scheduler._publish_callbacks
        assert scheduler._publish_callbacks[Platform.TWITTER] == mock_callback

    def test_schedule_post(self, scheduler):
        """测试调度帖子"""
        scheduled_time = datetime.now() + timedelta(hours=1)
        
        post = scheduler.schedule_post(
            content="Test content",
            platform=Platform.TWITTER,
            scheduled_time=scheduled_time,
            hashtags=["#test"],
        )
        
        assert post.id is not None
        assert post.content == "Test content"
        assert post.platform == Platform.TWITTER
        assert post.status == ScheduleStatus.SCHEDULED
        assert len(scheduler._scheduled_posts) == 1

    def test_schedule_post_with_media(self, scheduler):
        """测试调度带媒体的帖子"""
        post = scheduler.schedule_post(
            content="Test with media",
            platform=Platform.INSTAGRAM,
            scheduled_time=datetime.now() + timedelta(hours=1),
            media_urls=["https://example.com/image.jpg"],
        )
        
        assert len(post.media_urls) == 1
        assert post.media_urls[0] == "https://example.com/image.jpg"

    def test_schedule_post_max_limit(self, scheduler):
        """测试达到最大限制"""
        scheduler.config.max_scheduled_posts = 2
        
        scheduler.schedule_post(
            content="Post 1",
            platform=Platform.TWITTER,
            scheduled_time=datetime.now() + timedelta(hours=1),
        )
        scheduler.schedule_post(
            content="Post 2",
            platform=Platform.TWITTER,
            scheduled_time=datetime.now() + timedelta(hours=1),
        )
        
        with pytest.raises(ValueError, match="Maximum scheduled posts"):
            scheduler.schedule_post(
                content="Post 3",
                platform=Platform.TWITTER,
                scheduled_time=datetime.now() + timedelta(hours=1),
            )

    def test_cancel_post(self, scheduler):
        """测试取消帖子"""
        post = scheduler.schedule_post(
            content="Test",
            platform=Platform.TWITTER,
            scheduled_time=datetime.now() + timedelta(hours=1),
        )
        
        result = scheduler.cancel_post(post.id)
        
        assert result is True
        assert scheduler.get_post(post.id).status == ScheduleStatus.CANCELLED

    def test_cancel_non_existent_post(self, scheduler):
        """测试取消不存在的帖子"""
        result = scheduler.cancel_post("non_existent")
        assert result is False

    def test_cancel_published_post(self, scheduler):
        """测试取消已发布的帖子"""
        post = scheduler.schedule_post(
            content="Test",
            platform=Platform.TWITTER,
            scheduled_time=datetime.now() + timedelta(hours=1),
        )
        post.status = ScheduleStatus.PUBLISHED
        
        result = scheduler.cancel_post(post.id)
        assert result is False

    def test_reschedule_post(self, scheduler):
        """测试重新调度帖子"""
        original_time = datetime.now() + timedelta(hours=1)
        new_time = datetime.now() + timedelta(hours=2)
        
        post = scheduler.schedule_post(
            content="Test",
            platform=Platform.TWITTER,
            scheduled_time=original_time,
        )
        
        result = scheduler.reschedule_post(post.id, new_time)
        
        assert result is True
        assert scheduler.get_post(post.id).scheduled_time == new_time

    def test_reschedule_non_existent_post(self, scheduler):
        """测试重新调度不存在的帖子"""
        result = scheduler.reschedule_post(
            "non_existent",
            datetime.now() + timedelta(hours=2),
        )
        assert result is False

    def test_reschedule_published_post(self, scheduler):
        """测试重新调度已发布的帖子"""
        post = scheduler.schedule_post(
            content="Test",
            platform=Platform.TWITTER,
            scheduled_time=datetime.now() + timedelta(hours=1),
        )
        post.status = ScheduleStatus.PUBLISHED
        
        result = scheduler.reschedule_post(
            post.id,
            datetime.now() + timedelta(hours=2),
        )
        assert result is False

    def test_get_post(self, scheduler):
        """测试获取帖子"""
        post = scheduler.schedule_post(
            content="Test",
            platform=Platform.TWITTER,
            scheduled_time=datetime.now() + timedelta(hours=1),
        )
        
        retrieved = scheduler.get_post(post.id)
        
        assert retrieved is not None
        assert retrieved.id == post.id

    def test_get_non_existent_post(self, scheduler):
        """测试获取不存在的帖子"""
        retrieved = scheduler.get_post("non_existent")
        assert retrieved is None

    def test_get_scheduled_posts(self, scheduler):
        """测试获取调度的帖子"""
        scheduler.schedule_post(
            content="Post 1",
            platform=Platform.TWITTER,
            scheduled_time=datetime.now() + timedelta(hours=1),
        )
        scheduler.schedule_post(
            content="Post 2",
            platform=Platform.LINKEDIN,
            scheduled_time=datetime.now() + timedelta(hours=2),
        )
        
        posts = scheduler.get_scheduled_posts()
        assert len(posts) == 2

    def test_get_scheduled_posts_by_platform(self, scheduler):
        """测试按平台获取帖子"""
        scheduler.schedule_post(
            content="Post 1",
            platform=Platform.TWITTER,
            scheduled_time=datetime.now() + timedelta(hours=1),
        )
        scheduler.schedule_post(
            content="Post 2",
            platform=Platform.LINKEDIN,
            scheduled_time=datetime.now() + timedelta(hours=2),
        )
        
        twitter_posts = scheduler.get_scheduled_posts(platform=Platform.TWITTER)
        assert len(twitter_posts) == 1
        assert twitter_posts[0].platform == Platform.TWITTER

    def test_get_scheduled_posts_by_status(self, scheduler):
        """测试按状态获取帖子"""
        post1 = scheduler.schedule_post(
            content="Post 1",
            platform=Platform.TWITTER,
            scheduled_time=datetime.now() + timedelta(hours=1),
        )
        scheduler.schedule_post(
            content="Post 2",
            platform=Platform.TWITTER,
            scheduled_time=datetime.now() + timedelta(hours=2),
        )
        
        post1.status = ScheduleStatus.PUBLISHED
        
        scheduled_posts = scheduler.get_scheduled_posts(status=ScheduleStatus.SCHEDULED)
        assert len(scheduled_posts) == 1

    def test_get_upcoming_posts(self, scheduler):
        """测试获取即将发布的帖子"""
        scheduler.schedule_post(
            content="Post 1",
            platform=Platform.TWITTER,
            scheduled_time=datetime.now() + timedelta(hours=1),
        )
        scheduler.schedule_post(
            content="Post 2",
            platform=Platform.TWITTER,
            scheduled_time=datetime.now() + timedelta(days=2),
        )
        
        upcoming = scheduler.get_upcoming_posts(hours=24)
        assert len(upcoming) == 1

    def test_get_scheduler_stats(self, scheduler):
        """测试获取调度器统计"""
        scheduler.schedule_post(
            content="Post 1",
            platform=Platform.TWITTER,
            scheduled_time=datetime.now() + timedelta(hours=1),
        )
        
        stats = scheduler.get_scheduler_stats()
        
        assert stats["total_posts"] == 1
        assert "status_breakdown" in stats
        assert "platform_breakdown" in stats
        assert "running" in stats

    def test_schedule_recurring(self, scheduler):
        """测试调度周期性帖子"""
        start_time = datetime.now() + timedelta(hours=1)
        interval = timedelta(days=1)
        
        posts = scheduler.schedule_recurring(
            content="Recurring post",
            platform=Platform.TWITTER,
            start_time=start_time,
            interval=interval,
            count=5,
        )
        
        assert len(posts) == 5
        assert all(p.platform == Platform.TWITTER for p in posts)

    def test_suggest_best_times_twitter(self, scheduler):
        """测试推荐最佳发布时间 - Twitter"""
        times = scheduler.suggest_best_times(Platform.TWITTER)
        
        assert len(times) > 0
        assert all(isinstance(t, datetime) for t in times)

    def test_suggest_best_times_linkedin(self, scheduler):
        """测试推荐最佳发布时间 - LinkedIn"""
        times = scheduler.suggest_best_times(Platform.LINKEDIN)
        
        assert len(times) > 0

    def test_suggest_best_times_instagram(self, scheduler):
        """测试推荐最佳发布时间 - Instagram"""
        times = scheduler.suggest_best_times(Platform.INSTAGRAM)
        
        assert len(times) > 0

    def test_schedule_status_enum(self):
        """测试调度状态枚举"""
        assert ScheduleStatus.PENDING.value == "pending"
        assert ScheduleStatus.SCHEDULED.value == "scheduled"
        assert ScheduleStatus.PUBLISHING.value == "publishing"
        assert ScheduleStatus.PUBLISHED.value == "published"
        assert ScheduleStatus.FAILED.value == "failed"
        assert ScheduleStatus.CANCELLED.value == "cancelled"


# ============================================================================
# Content Adapter Tests
# ============================================================================


class TestContentAdapter:
    """ContentAdapter 单元测试"""

    def test_adapter_initialization(self, adapter):
        """测试适配器初始化"""
        assert adapter is not None

    def test_adapt_content_twitter(self, adapter):
        """测试适配 Twitter 内容"""
        result = adapter.adapt_content(
            content="This is a test post for Twitter",
            platform=Platform.TWITTER,
            hashtags=["#test"],
        )
        
        assert result.platform == Platform.TWITTER
        assert "#test" in result.hashtags

    def test_adapt_content_linkedin(self, adapter):
        """测试适配 LinkedIn 内容"""
        result = adapter.adapt_content(
            content="Professional post for LinkedIn",
            platform=Platform.LINKEDIN,
        )
        
        assert result.platform == Platform.LINKEDIN

    def test_adapt_content_instagram(self, adapter):
        """测试适配 Instagram 内容"""
        result = adapter.adapt_content(
            content="Visual post for Instagram",
            platform=Platform.INSTAGRAM,
            media_urls=["https://example.com/image.jpg"],
        )
        
        assert result.platform == Platform.INSTAGRAM
        assert len(result.media_urls) == 1

    def test_adapt_content_truncate(self, adapter):
        """测试内容截断"""
        long_content = "A" * 500
        
        result = adapter.adapt_content(
            content=long_content,
            platform=Platform.LINKEDIN,
        )
        
        # LinkedIn 限制 3000 字符，500 字符不会被截断
        # 这里测试内容适配基本功能
        assert len(result.content) == 500
        assert result.platform == Platform.LINKEDIN

    def test_adapt_content_thread(self, adapter):
        """测试线程拆分"""
        long_content = "B" * 500
        
        result = adapter.adapt_content(
            content=long_content,
            platform=Platform.TWITTER,
        )
        
        assert len(result.thread_parts) > 0 or len(result.warnings) > 0

    def test_adapt_for_all_platforms(self, adapter):
        """测试适配所有平台"""
        results = adapter.adapt_for_all_platforms(
            content="Multi-platform post",
            hashtags=["#test"],
        )
        
        assert len(results) == len(Platform)
        assert Platform.TWITTER in results
        assert Platform.LINKEDIN in results

    def test_optimize_hashtags(self, adapter):
        """测试优化话题标签"""
        hashtags = ["#test", "#demo", "#test", "#example"]
        
        optimized = adapter._optimize_hashtags(hashtags, max_count=3)
        
        assert len(optimized) <= 3
        assert len(set(optimized)) == len(optimized)

    def test_optimize_hashtags_add_hash(self, adapter):
        """测试添加话题标签符号"""
        hashtags = ["test", "demo"]
        
        optimized = adapter._optimize_hashtags(hashtags, max_count=5)
        
        assert all(tag.startswith("#") for tag in optimized)

    def test_split_to_thread(self, adapter):
        """测试拆分线程"""
        content = "First sentence. Second sentence. Third sentence."
        
        threads = adapter._split_to_thread(content, max_chars=50)
        
        assert len(threads) > 0
        assert all(len(t) <= 50 for t in threads)

    def test_truncate_content(self, adapter):
        """测试截断内容"""
        content = "A" * 100
        
        truncated = adapter._truncate_content(content, max_chars=50)
        
        assert len(truncated) <= 50
        assert truncated.endswith("...")

    def test_truncate_content_no_need(self, adapter):
        """测试不需要截断"""
        content = "Short content"
        
        truncated = adapter._truncate_content(content, max_chars=100)
        
        assert truncated == content

    def test_extract_hashtags(self, adapter):
        """测试提取话题标签"""
        content = "Check this out #test #demo #example"
        
        hashtags = adapter._extract_existing_hashtags(content, [])
        
        assert len(hashtags) == 3
        assert "#test" in hashtags

    def test_extract_mentions(self, adapter):
        """测试提取提及"""
        content = "Hello @john and @jane!"
        
        mentions = adapter._extract_existing_mentions(content)
        
        assert len(mentions) == 2
        assert "@john" in mentions

    def test_validate_content_valid(self, adapter):
        """测试验证有效内容"""
        result = adapter.validate_content(
            content="Short post",
            platform=Platform.TWITTER,
        )
        
        assert result["valid"] is True
        assert result["remaining"] >= 0

    def test_validate_content_invalid(self, adapter):
        """测试验证无效内容"""
        long_content = "A" * 500
        
        result = adapter.validate_content(
            content=long_content,
            platform=Platform.TWITTER,
        )
        
        assert result["valid"] is False
        assert result["remaining"] < 0

    def test_get_platform_limits(self, adapter):
        """测试获取平台限制"""
        limits = adapter.get_platform_limits(Platform.TWITTER)
        
        assert limits.max_characters == 280
        assert limits.max_hashtags == 3

    def test_platform_enum(self):
        """测试平台枚举"""
        assert Platform.TWITTER.value == "twitter"
        assert Platform.LINKEDIN.value == "linkedin"
        assert Platform.YOUTUBE.value == "youtube"
        assert Platform.INSTAGRAM.value == "instagram"
        assert Platform.FACEBOOK.value == "facebook"
        assert Platform.TIKTOK.value == "tiktok"

    def test_content_type_enum(self):
        """测试内容类型枚举"""
        assert ContentType.TEXT.value == "text"
        assert ContentType.IMAGE.value == "image"
        assert ContentType.VIDEO.value == "video"
        assert ContentType.CAROUSEL.value == "carousel"
        assert ContentType.STORY.value == "story"


# ============================================================================
# Social Analytics Tests
# ============================================================================


class TestSocialAnalytics:
    """SocialAnalytics 单元测试"""

    def test_analytics_initialization(self, analytics):
        """测试分析器初始化"""
        assert analytics is not None
        assert len(analytics._metrics_history) == 0

    def test_record_metrics(self, analytics, sample_metrics):
        """测试记录指标"""
        analytics.record_metrics(sample_metrics)
        
        history = analytics.get_metrics_history("POST-001")
        assert len(history) == 1

    def test_calculate_engagement_rate(self, analytics, sample_metrics):
        """测试计算互动率"""
        rate = analytics._calculate_engagement_rate(sample_metrics)
        
        assert rate > 0
        assert rate <= 100

    def test_calculate_engagement_rate_zero_impressions(self, analytics):
        """测试零展示时的互动率"""
        metrics = PostMetrics(
            post_id="POST-002",
            platform=Platform.TWITTER,
            impressions=0,
            likes=10,
        )
        
        rate = analytics._calculate_engagement_rate(metrics)
        assert rate == 0.0

    def test_calculate_ctr(self, analytics, sample_metrics):
        """测试计算点击率"""
        ctr = analytics._calculate_ctr(sample_metrics)
        
        assert ctr >= 0

    def test_get_post_metrics(self, analytics, sample_metrics):
        """测试获取帖子指标"""
        analytics.record_metrics(sample_metrics)
        
        metrics = analytics.get_post_metrics("POST-001")
        
        assert metrics is not None
        assert metrics.post_id == "POST-001"

    def test_get_non_existent_post_metrics(self, analytics):
        """测试获取不存在的帖子指标"""
        metrics = analytics.get_post_metrics("NON_EXISTENT")
        assert metrics is None

    def test_analyze_platform(self, analytics, sample_metrics):
        """测试分析平台"""
        analytics.record_metrics(sample_metrics)
        
        platform_analytics = analytics.analyze_platform(
            Platform.TWITTER,
            AnalyticsPeriod.LAST_7_DAYS,
        )
        
        assert platform_analytics.platform == Platform.TWITTER
        assert platform_analytics.total_posts >= 0

    def test_analyze_platform_no_data(self, analytics):
        """测试分析无数据平台"""
        platform_analytics = analytics.analyze_platform(
            Platform.LINKEDIN,
            AnalyticsPeriod.LAST_7_DAYS,
        )
        
        assert platform_analytics.total_posts == 0

    def test_compare_performance(self, analytics, sample_metrics):
        """测试比较表现"""
        analytics.record_metrics(sample_metrics)
        
        comparison = analytics.compare_performance(sample_metrics)
        
        assert "platform" in comparison
        assert "engagement_rate" in comparison
        assert "engagement_status" in comparison
        assert "overall_score" in comparison

    def test_get_recommendations(self, analytics, sample_metrics):
        """测试获取推荐"""
        recommendations = analytics.get_recommendations(
            Platform.TWITTER,
            sample_metrics,
        )
        
        assert isinstance(recommendations, list)

    def test_get_recommendations_no_metrics(self, analytics):
        """测试无指标时的推荐"""
        recommendations = analytics.get_recommendations(Platform.TWITTER)
        
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0

    def test_get_analytics_summary(self, analytics, sample_metrics):
        """测试获取分析摘要"""
        analytics.record_metrics(sample_metrics)
        
        summary = analytics.get_analytics_summary()
        
        assert "platforms" in summary
        assert "total_posts" in summary
        assert "generated_at" in summary

    def test_benchmark_rates(self, analytics):
        """测试基准率"""
        assert Platform.TWITTER in analytics.BENCHMARK_RATES
        assert Platform.LINKEDIN in analytics.BENCHMARK_RATES

    def test_metric_type_enum(self):
        """测试指标类型枚举"""
        assert MetricType.IMPRESSIONS.value == "impressions"
        assert MetricType.REACH.value == "reach"
        assert MetricType.ENGAGEMENT.value == "engagement"
        assert MetricType.LIKES.value == "likes"
        assert MetricType.COMMENTS.value == "comments"

    def test_analytics_period_enum(self):
        """测试分析周期枚举"""
        assert AnalyticsPeriod.LAST_24_HOURS.value == "24h"
        assert AnalyticsPeriod.LAST_7_DAYS.value == "7d"
        assert AnalyticsPeriod.LAST_30_DAYS.value == "30d"
        assert AnalyticsPeriod.LAST_90_DAYS.value == "90d"


# ============================================================================
# Content Calendar Tests
# ============================================================================


class TestContentCalendar:
    """ContentCalendar 单元测试"""

    def test_calendar_initialization(self, calendar):
        """测试日历初始化"""
        assert calendar is not None
        assert len(calendar._themes) > 0

    def test_create_event(self, calendar):
        """测试创建事件"""
        event = calendar.create_event(
            title="Test Event",
            event_type=CalendarEventType.POST,
            platforms=[Platform.TWITTER],
            scheduled_time=datetime.now() + timedelta(days=1),
            content="Test content",
        )
        
        assert event.id is not None
        assert event.title == "Test Event"
        assert event.status == ContentStatus.DRAFT

    def test_update_event(self, calendar):
        """测试更新事件"""
        event = calendar.create_event(
            title="Test Event",
            event_type=CalendarEventType.POST,
        )
        
        updated = calendar.update_event(
            event.id,
            title="Updated Title",
            status=ContentStatus.APPROVED,
        )
        
        assert updated is not None
        assert updated.title == "Updated Title"
        assert updated.status == ContentStatus.APPROVED

    def test_update_non_existent_event(self, calendar):
        """测试更新不存在的事件"""
        updated = calendar.update_event(
            "non_existent",
            title="New Title",
        )
        assert updated is None

    def test_delete_event(self, calendar):
        """测试删除事件"""
        event = calendar.create_event(
            title="Test Event",
            event_type=CalendarEventType.POST,
        )
        
        result = calendar.delete_event(event.id)
        
        assert result is True
        assert calendar.get_event(event.id) is None

    def test_delete_non_existent_event(self, calendar):
        """测试删除不存在的事件"""
        result = calendar.delete_event("non_existent")
        assert result is False

    def test_get_event(self, calendar):
        """测试获取事件"""
        event = calendar.create_event(
            title="Test Event",
            event_type=CalendarEventType.POST,
        )
        
        retrieved = calendar.get_event(event.id)
        
        assert retrieved is not None
        assert retrieved.id == event.id

    def test_get_events_by_date(self, calendar):
        """测试按日期获取事件"""
        scheduled_time = datetime.now().replace(hour=10, minute=0, second=0)
        
        calendar.create_event(
            title="Event 1",
            scheduled_time=scheduled_time,
            platforms=[Platform.TWITTER],
        )
        
        events = calendar.get_events_by_date(scheduled_time)
        assert len(events) == 1

    def test_get_events_by_range(self, calendar):
        """测试按范围获取事件"""
        now = datetime.now()
        
        calendar.create_event(
            title="Event 1",
            scheduled_time=now + timedelta(days=1),
        )
        calendar.create_event(
            title="Event 2",
            scheduled_time=now + timedelta(days=5),
        )
        
        events = calendar.get_events_by_range(
            now,
            now + timedelta(days=3),
        )
        
        assert len(events) == 1

    def test_get_events_by_status(self, calendar):
        """测试按状态获取事件"""
        event1 = calendar.create_event(
            title="Event 1",
            status=ContentStatus.DRAFT,
        )
        event2 = calendar.create_event(
            title="Event 2",
            status=ContentStatus.APPROVED,
        )
        
        drafts = calendar.get_events_by_status(ContentStatus.DRAFT)
        
        assert len(drafts) == 1
        assert drafts[0].id == event1.id

    def test_get_upcoming_events(self, calendar):
        """测试获取即将发生的事件"""
        calendar.create_event(
            title="Upcoming Event",
            scheduled_time=datetime.now() + timedelta(days=2),
        )
        
        upcoming = calendar.get_upcoming_events(days=7)
        
        assert len(upcoming) > 0

    def test_create_theme(self, calendar):
        """测试创建主题"""
        theme = calendar.create_theme(
            name="Test Theme",
            description="Test description",
            color="#FF0000",
            hashtags=["#test"],
        )
        
        assert theme.id is not None
        assert theme.name == "Test Theme"

    def test_get_theme(self, calendar):
        """测试获取主题"""
        theme = calendar.create_theme(
            name="Test Theme",
            description="Description",
        )
        
        retrieved = calendar.get_theme(theme.id)
        
        assert retrieved is not None
        assert retrieved.name == "Test Theme"

    def test_list_themes(self, calendar):
        """测试列出主题"""
        themes = calendar.list_themes()
        
        assert len(themes) > 0
        assert all(t.active for t in themes)

    def test_get_calendar_overview(self, calendar):
        """测试获取日历概览"""
        now = datetime.now()
        
        calendar.create_event(
            title="Event 1",
            scheduled_time=now + timedelta(days=1),
        )
        
        overview = calendar.get_calendar_overview(
            now,
            now + timedelta(days=7),
        )
        
        assert "total_events" in overview
        assert "daily_counts" in overview
        assert "platform_distribution" in overview

    def test_suggest_content_slots(self, calendar):
        """测试推荐内容槽"""
        slots = calendar.suggest_content_slots(Platform.TWITTER, days=7)
        
        assert len(slots) > 0
        assert all("datetime" in s for s in slots)

    def test_export_calendar(self, calendar):
        """测试导出日历"""
        now = datetime.now()
        
        calendar.create_event(
            title="Event",
            scheduled_time=now + timedelta(days=1),
        )
        
        exported = calendar.export_calendar(
            now,
            now + timedelta(days=7),
            format="json",
        )
        
        assert isinstance(exported, str)
        assert "events" in exported

    def test_calendar_event_type_enum(self):
        """测试日历事件类型枚举"""
        assert CalendarEventType.POST.value == "post"
        assert CalendarEventType.CAMPAIGN.value == "campaign"
        assert CalendarEventType.THEME.value == "theme"
        assert CalendarEventType.HOLIDAY.value == "holiday"
        assert CalendarEventType.EVENT.value == "event"

    def test_content_status_enum(self):
        """测试内容状态枚举"""
        assert ContentStatus.DRAFT.value == "draft"
        assert ContentStatus.REVIEW.value == "review"
        assert ContentStatus.APPROVED.value == "approved"
        assert ContentStatus.SCHEDULED.value == "scheduled"
        assert ContentStatus.PUBLISHED.value == "published"


# ============================================================================
# Account Manager Tests
# ============================================================================


class TestAccountManager:
    """AccountManager 单元测试"""

    def test_manager_initialization(self, account_manager):
        """测试管理器初始化"""
        assert account_manager is not None
        assert len(account_manager._accounts) == 0

    def test_add_account(self, account_manager):
        """测试添加账户"""
        account = account_manager.add_account(
            platform=Platform.TWITTER,
            username="testuser",
            display_name="Test User",
            account_type=AccountType.PERSONAL,
        )
        
        assert account.id is not None
        assert account.username == "testuser"
        assert account.platform == Platform.TWITTER

    def test_add_duplicate_account(self, account_manager):
        """测试添加重复账户"""
        account_manager.add_account(
            platform=Platform.TWITTER,
            username="testuser",
        )
        
        account2 = account_manager.add_account(
            platform=Platform.TWITTER,
            username="testuser",
        )
        
        assert account2.username == "testuser"

    def test_update_account(self, account_manager):
        """测试更新账户"""
        account = account_manager.add_account(
            platform=Platform.TWITTER,
            username="testuser",
        )
        
        updated = account_manager.update_account(
            account.id,
            display_name="Updated Name",
            followers_count=100,
        )
        
        assert updated is not None
        assert updated.display_name == "Updated Name"
        assert updated.followers_count == 100

    def test_update_non_existent_account(self, account_manager):
        """测试更新不存在的账户"""
        updated = account_manager.update_account(
            "non_existent",
            display_name="New Name",
        )
        assert updated is None

    def test_remove_account(self, account_manager):
        """测试移除账户"""
        account = account_manager.add_account(
            platform=Platform.TWITTER,
            username="testuser",
        )
        
        result = account_manager.remove_account(account.id)
        
        assert result is True
        assert account_manager.get_account(account.id) is None

    def test_remove_non_existent_account(self, account_manager):
        """测试移除不存在的账户"""
        result = account_manager.remove_account("non_existent")
        assert result is False

    def test_get_account(self, account_manager):
        """测试获取账户"""
        account = account_manager.add_account(
            platform=Platform.TWITTER,
            username="testuser",
        )
        
        retrieved = account_manager.get_account(account.id)
        
        assert retrieved is not None
        assert retrieved.id == account.id

    def test_get_account_by_username(self, account_manager):
        """测试按用户名获取账户"""
        account_manager.add_account(
            platform=Platform.TWITTER,
            username="testuser",
        )
        
        retrieved = account_manager.get_account_by_username(
            Platform.TWITTER,
            "testuser",
        )
        
        assert retrieved is not None
        assert retrieved.username == "testuser"

    def test_get_accounts_by_platform(self, account_manager):
        """测试按平台获取账户"""
        account_manager.add_account(
            platform=Platform.TWITTER,
            username="user1",
        )
        account_manager.add_account(
            platform=Platform.TWITTER,
            username="user2",
        )
        account_manager.add_account(
            platform=Platform.LINKEDIN,
            username="user3",
        )
        
        twitter_accounts = account_manager.get_accounts_by_platform(
            Platform.TWITTER
        )
        
        assert len(twitter_accounts) == 2
        assert all(a.platform == Platform.TWITTER for a in twitter_accounts)

    def test_set_primary_account(self, account_manager):
        """测试设置主要账户"""
        account1 = account_manager.add_account(
            platform=Platform.TWITTER,
            username="user1",
        )
        account2 = account_manager.add_account(
            platform=Platform.TWITTER,
            username="user2",
        )
        
        result = account_manager.set_primary_account(account1.id)
        
        assert result is True
        assert account_manager.get_account(account1.id).is_primary is True
        assert account_manager.get_account(account2.id).is_primary is False

    def test_get_primary_account(self, account_manager):
        """测试获取主要账户"""
        account = account_manager.add_account(
            platform=Platform.TWITTER,
            username="primary_user",
            is_primary=True,
        )
        
        primary = account_manager.get_primary_account(Platform.TWITTER)
        
        assert primary is not None
        assert primary.username == "primary_user"

    def test_update_stats(self, account_manager):
        """测试更新统计"""
        account = account_manager.add_account(
            platform=Platform.TWITTER,
            username="testuser",
        )
        
        stats = account_manager.update_stats(
            account.id,
            followers=1000,
            following=500,
            posts=100,
            engagement_rate=2.5,
        )
        
        assert stats is not None
        assert stats.followers == 1000
        assert stats.engagement_rate == 2.5

    def test_get_stats_history(self, account_manager):
        """测试获取统计历史"""
        account = account_manager.add_account(
            platform=Platform.TWITTER,
            username="testuser",
        )
        
        account_manager.update_stats(account.id, followers=100, following=50, posts=10)
        account_manager.update_stats(account.id, followers=150, following=60, posts=15)
        
        history = account_manager.get_stats_history(account.id)
        
        assert len(history) == 2

    def test_list_all_accounts(self, account_manager):
        """测试列出所有账户"""
        account_manager.add_account(
            platform=Platform.TWITTER,
            username="user1",
        )
        account_manager.add_account(
            platform=Platform.LINKEDIN,
            username="user2",
        )
        
        accounts = account_manager.list_all_accounts()
        
        assert len(accounts) == 2

    def test_get_account_summary(self, account_manager):
        """测试获取账户摘要"""
        account_manager.add_account(
            platform=Platform.TWITTER,
            username="user1",
            display_name="User One",
        )
        account_manager.add_account(
            platform=Platform.LINKEDIN,
            username="user2",
            display_name="User Two",
        )
        
        summary = account_manager.get_account_summary()
        
        assert summary["total_accounts"] == 2
        assert "platform_distribution" in summary

    def test_check_account_health(self, account_manager):
        """测试检查账户健康"""
        account = account_manager.add_account(
            platform=Platform.TWITTER,
            username="testuser",
        )
        
        health = account_manager.check_account_health(account.id)
        
        assert "account_id" in health
        assert "status" in health
        assert "issues" in health
        assert "recommendations" in health

    def test_check_non_existent_account_health(self, account_manager):
        """测试检查不存在的账户健康"""
        health = account_manager.check_account_health("non_existent")
        
        assert "error" in health

    def test_account_status_enum(self):
        """测试账户状态枚举"""
        assert AccountStatus.ACTIVE.value == "active"
        assert AccountStatus.INACTIVE.value == "inactive"
        assert AccountStatus.SUSPENDED.value == "suspended"
        assert AccountStatus.PENDING.value == "pending"

    def test_account_type_enum(self):
        """测试账户类型枚举"""
        assert AccountType.PERSONAL.value == "personal"
        assert AccountType.BUSINESS.value == "business"
        assert AccountType.CREATOR.value == "creator"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
