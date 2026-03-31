"""
Tests for Social Media Module
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

from agentforge.social.content_adapter import (
    ContentAdapter,
    Platform,
    ContentType,
    AdaptedContent,
    content_adapter
)
from agentforge.social.scheduler import (
    PostScheduler,
    ScheduledPost,
    ScheduleStatus,
    ScheduleConfig
)
from agentforge.social.analytics import (
    SocialAnalytics,
    PostMetrics,
    AnalyticsPeriod
)
from agentforge.social.calendar import (
    ContentCalendar,
    CalendarEvent,
    CalendarEventType,
    ContentStatus
)
from agentforge.social.account_manager import (
    AccountManager,
    SocialAccount,
    AccountStatus,
    AccountType
)


class TestContentAdapter:
    """Tests for ContentAdapter"""
    
    @pytest.fixture
    def adapter(self):
        return ContentAdapter()
    
    def test_platform_enum(self):
        assert Platform.TWITTER.value == "twitter"
        assert Platform.LINKEDIN.value == "linkedin"
        assert Platform.INSTAGRAM.value == "instagram"
    
    def test_adapt_content_twitter(self, adapter):
        content = "This is a test post for Twitter"
        adapted = adapter.adapt_content(content, Platform.TWITTER)
        
        assert adapted.platform == Platform.TWITTER
        assert adapted.content == content
        assert len(adapted.warnings) == 0
    
    def test_adapt_content_truncation(self, adapter):
        long_content = "A" * 3000
        adapted = adapter.adapt_content(long_content, Platform.INSTAGRAM)
        
        assert len(adapted.content) <= 2200
        assert len(adapted.warnings) > 0
    
    def test_adapt_content_thread_split(self, adapter):
        long_content = "This is sentence one. " * 50
        adapted = adapter.adapt_content(long_content, Platform.TWITTER)
        
        if adapted.thread_parts:
            assert len(adapted.thread_parts) > 1
    
    def test_optimize_hashtags(self, adapter):
        hashtags = ["python", "#coding", "test", "#python"]
        optimized = adapter._optimize_hashtags(hashtags, 3)
        
        assert len(optimized) <= 3
        assert all(tag.startswith('#') for tag in optimized)
    
    def test_extract_hashtags(self, adapter):
        content = "This is a #test post with #hashtags"
        existing = ["#existing"]
        hashtags = adapter._extract_existing_hashtags(content, existing)
        
        assert "#test" in hashtags
        assert "#hashtags" in hashtags
        assert "#existing" in hashtags
    
    def test_extract_mentions(self, adapter):
        content = "Hello @user1 and @user2!"
        mentions = adapter._extract_existing_mentions(content)
        
        assert "@user1" in mentions
        assert "@user2" in mentions
    
    def test_adapt_for_all_platforms(self, adapter):
        content = "Test post"
        results = adapter.adapt_for_all_platforms(
            content,
            platforms=[Platform.TWITTER, Platform.LINKEDIN]
        )
        
        assert Platform.TWITTER in results
        assert Platform.LINKEDIN in results
    
    def test_validate_content(self, adapter):
        content = "Test content"
        validation = adapter.validate_content(content, Platform.TWITTER)
        
        assert validation["valid"] is True
        assert validation["length"] == len(content)
        assert validation["max_length"] == 280


class TestPostScheduler:
    """Tests for PostScheduler"""
    
    @pytest.fixture
    def scheduler(self):
        return PostScheduler(config=ScheduleConfig())
    
    def test_schedule_post(self, scheduler):
        scheduled_time = datetime.now() + timedelta(hours=1)
        post = scheduler.schedule_post(
            content="Test post",
            platform=Platform.TWITTER,
            scheduled_time=scheduled_time
        )
        
        assert post.content == "Test post"
        assert post.platform == Platform.TWITTER
        assert post.status == ScheduleStatus.SCHEDULED
    
    def test_cancel_post(self, scheduler):
        scheduled_time = datetime.now() + timedelta(hours=1)
        post = scheduler.schedule_post(
            content="Test post",
            platform=Platform.TWITTER,
            scheduled_time=scheduled_time
        )
        
        result = scheduler.cancel_post(post.id)
        
        assert result is True
        assert post.status == ScheduleStatus.CANCELLED
    
    def test_reschedule_post(self, scheduler):
        original_time = datetime.now() + timedelta(hours=1)
        post = scheduler.schedule_post(
            content="Test post",
            platform=Platform.TWITTER,
            scheduled_time=original_time
        )
        
        new_time = datetime.now() + timedelta(hours=2)
        result = scheduler.reschedule_post(post.id, new_time)
        
        assert result is True
        assert post.scheduled_time == new_time
    
    def test_get_scheduled_posts(self, scheduler):
        scheduled_time = datetime.now() + timedelta(hours=1)
        scheduler.schedule_post(
            content="Test post 1",
            platform=Platform.TWITTER,
            scheduled_time=scheduled_time
        )
        scheduler.schedule_post(
            content="Test post 2",
            platform=Platform.LINKEDIN,
            scheduled_time=scheduled_time
        )
        
        posts = scheduler.get_scheduled_posts()
        
        assert len(posts) == 2
    
    def test_get_upcoming_posts(self, scheduler):
        scheduled_time = datetime.now() + timedelta(hours=1)
        scheduler.schedule_post(
            content="Test post",
            platform=Platform.TWITTER,
            scheduled_time=scheduled_time
        )
        
        upcoming = scheduler.get_upcoming_posts(hours=24)
        
        assert len(upcoming) == 1
    
    def test_suggest_best_times(self, scheduler):
        suggestions = scheduler.suggest_best_times(Platform.TWITTER)
        
        assert len(suggestions) > 0
        assert all(isinstance(t, datetime) for t in suggestions)
    
    def test_scheduler_stats(self, scheduler):
        stats = scheduler.get_scheduler_stats()
        
        assert "total_posts" in stats
        assert "running" in stats


class TestSocialAnalytics:
    """Tests for SocialAnalytics"""
    
    @pytest.fixture
    def analytics(self):
        return SocialAnalytics()
    
    @pytest.fixture
    def sample_metrics(self):
        return PostMetrics(
            post_id="post-001",
            platform=Platform.TWITTER,
            impressions=1000,
            reach=800,
            likes=50,
            comments=10,
            shares=5,
            clicks=20
        )
    
    def test_record_metrics(self, analytics, sample_metrics):
        analytics.record_metrics(sample_metrics)
        
        retrieved = analytics.get_post_metrics("post-001")
        
        assert retrieved is not None
        assert retrieved.post_id == "post-001"
    
    def test_calculate_engagement_rate(self, analytics, sample_metrics):
        analytics.record_metrics(sample_metrics)
        
        rate = sample_metrics.engagement_rate
        
        expected = ((50 + 10 + 5 + 20) / 1000) * 100
        assert rate == round(expected, 2)
    
    def test_analyze_platform(self, analytics, sample_metrics):
        analytics.record_metrics(sample_metrics)
        
        analysis = analytics.analyze_platform(Platform.TWITTER)
        
        assert analysis.platform == Platform.TWITTER
        assert analysis.total_posts > 0
    
    def test_compare_performance(self, analytics, sample_metrics):
        analytics.record_metrics(sample_metrics)
        
        comparison = analytics.compare_performance(sample_metrics)
        
        assert "engagement_rate" in comparison
        assert "benchmark_engagement" in comparison
        assert "overall_score" in comparison
    
    def test_get_recommendations(self, analytics):
        recommendations = analytics.get_recommendations(Platform.TWITTER)
        
        assert len(recommendations) > 0
    
    def test_analytics_summary(self, analytics, sample_metrics):
        analytics.record_metrics(sample_metrics)
        
        summary = analytics.get_analytics_summary()
        
        assert "platforms" in summary
        assert "total_posts" in summary


class TestContentCalendar:
    """Tests for ContentCalendar"""
    
    @pytest.fixture
    def calendar(self):
        return ContentCalendar()
    
    def test_create_event(self, calendar):
        event = calendar.create_event(
            title="Test Event",
            event_type=CalendarEventType.POST,
            platforms=[Platform.TWITTER]
        )
        
        assert event.title == "Test Event"
        assert event.event_type == CalendarEventType.POST
        assert Platform.TWITTER in event.platforms
    
    def test_update_event(self, calendar):
        event = calendar.create_event(title="Test Event")
        
        updated = calendar.update_event(event.id, title="Updated Title")
        
        assert updated.title == "Updated Title"
    
    def test_delete_event(self, calendar):
        event = calendar.create_event(title="Test Event")
        
        result = calendar.delete_event(event.id)
        
        assert result is True
        assert calendar.get_event(event.id) is None
    
    def test_get_events_by_date(self, calendar):
        scheduled_time = datetime.now().replace(hour=10, minute=0)
        calendar.create_event(
            title="Test Event",
            scheduled_time=scheduled_time
        )
        
        events = calendar.get_events_by_date(datetime.now())
        
        assert len(events) > 0
    
    def test_get_upcoming_events(self, calendar):
        scheduled_time = datetime.now() + timedelta(hours=1)
        calendar.create_event(
            title="Upcoming Event",
            scheduled_time=scheduled_time
        )
        
        upcoming = calendar.get_upcoming_events(days=1)
        
        assert len(upcoming) > 0
    
    def test_default_themes(self, calendar):
        themes = calendar.list_themes()
        
        assert len(themes) > 0
    
    def test_create_theme(self, calendar):
        theme = calendar.create_theme(
            name="Test Theme",
            description="Test description"
        )
        
        assert theme.name == "Test Theme"
    
    def test_suggest_content_slots(self, calendar):
        slots = calendar.suggest_content_slots(Platform.TWITTER, days=7)
        
        assert len(slots) > 0
    
    def test_calendar_overview(self, calendar):
        start = datetime.now()
        end = start + timedelta(days=7)
        
        overview = calendar.get_calendar_overview(start, end)
        
        assert "total_events" in overview
        assert "daily_counts" in overview


class TestAccountManager:
    """Tests for AccountManager"""
    
    @pytest.fixture
    def manager(self):
        return AccountManager()
    
    def test_add_account(self, manager):
        account = manager.add_account(
            platform=Platform.TWITTER,
            username="testuser"
        )
        
        assert account.username == "testuser"
        assert account.platform == Platform.TWITTER
    
    def test_add_duplicate_account(self, manager):
        manager.add_account(platform=Platform.TWITTER, username="testuser")
        
        duplicate = manager.add_account(platform=Platform.TWITTER, username="testuser")
        
        assert duplicate.is_primary is False
    
    def test_update_account(self, manager):
        account = manager.add_account(
            platform=Platform.TWITTER,
            username="testuser"
        )
        
        updated = manager.update_account(account.id, display_name="Test User")
        
        assert updated.display_name == "Test User"
    
    def test_remove_account(self, manager):
        account = manager.add_account(
            platform=Platform.TWITTER,
            username="testuser"
        )
        
        result = manager.remove_account(account.id)
        
        assert result is True
        assert manager.get_account(account.id) is None
    
    def test_get_accounts_by_platform(self, manager):
        manager.add_account(platform=Platform.TWITTER, username="user1")
        manager.add_account(platform=Platform.TWITTER, username="user2")
        manager.add_account(platform=Platform.LINKEDIN, username="user3")
        
        twitter_accounts = manager.get_accounts_by_platform(Platform.TWITTER)
        
        assert len(twitter_accounts) == 2
    
    def test_set_primary_account(self, manager):
        account1 = manager.add_account(
            platform=Platform.TWITTER,
            username="user1",
            is_primary=True
        )
        account2 = manager.add_account(
            platform=Platform.TWITTER,
            username="user2"
        )
        
        manager.set_primary_account(account2.id)
        
        assert account2.is_primary is True
        assert account1.is_primary is False
    
    def test_update_stats(self, manager):
        account = manager.add_account(
            platform=Platform.TWITTER,
            username="testuser"
        )
        
        stats = manager.update_stats(
            account_id=account.id,
            followers=1000,
            following=500,
            posts=100
        )
        
        assert stats.followers == 1000
        assert account.followers_count == 1000
    
    def test_account_summary(self, manager):
        manager.add_account(platform=Platform.TWITTER, username="user1")
        manager.add_account(platform=Platform.LINKEDIN, username="user2")
        
        summary = manager.get_account_summary()
        
        assert summary["total_accounts"] == 2
        assert "platform_distribution" in summary
    
    def test_check_account_health(self, manager):
        account = manager.add_account(
            platform=Platform.TWITTER,
            username="testuser"
        )
        
        health = manager.check_account_health(account.id)
        
        assert "status" in health
        assert "issues" in health


class TestModels:
    """Tests for model classes"""
    
    def test_adapted_content_model(self):
        content = AdaptedContent(
            platform=Platform.TWITTER,
            content="Test content",
            hashtags=["#test"],
            mentions=["@user"]
        )
        
        assert content.platform == Platform.TWITTER
        assert len(content.hashtags) == 1
    
    def test_scheduled_post_model(self):
        post = ScheduledPost(
            content="Test post",
            platform=Platform.TWITTER,
            scheduled_time=datetime.now() + timedelta(hours=1)
        )
        
        assert post.status == ScheduleStatus.PENDING
        assert post.retry_count == 0
    
    def test_post_metrics_model(self):
        metrics = PostMetrics(
            post_id="post-001",
            platform=Platform.TWITTER,
            impressions=1000
        )
        
        assert metrics.impressions == 1000
        assert metrics.engagement_rate == 0.0
    
    def test_calendar_event_model(self):
        event = CalendarEvent(
            title="Test Event",
            event_type=CalendarEventType.POST
        )
        
        assert event.status == ContentStatus.DRAFT
    
    def test_social_account_model(self):
        account = SocialAccount(
            platform=Platform.TWITTER,
            username="testuser"
        )
        
        assert account.status == AccountStatus.ACTIVE
        assert account.account_type == AccountType.PERSONAL
