"""
AgentForge 社区管理引擎单元测试
测试社区管理相关的业务逻辑
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

from agentforge.community.community_manager import (
    CommunityAutomation,
    CommunityMonitor,
    CommunityMetrics,
    CommentAnalyzer,
    ReplyGenerator,
    Comment,
    CommentSentiment,
    ReplyType,
    AutoReplyRule,
    ReplyTemplate,
)
from integrations.external.social_client import SocialPlatform


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def comment_analyzer():
    """创建评论分析器实例"""
    return CommentAnalyzer()


@pytest.fixture
def reply_generator():
    """创建回复生成器实例"""
    return ReplyGenerator()


@pytest.fixture
def community_monitor():
    """创建社区监控器实例"""
    return CommunityMonitor()


@pytest.fixture
def community_automation():
    """创建社区自动化实例"""
    return CommunityAutomation()


@pytest.fixture
def sample_comment():
    """示例评论"""
    return Comment(
        id="COMMENT-001",
        platform=SocialPlatform.FACEBOOK,
        post_id="POST-001",
        author="test_user",
        author_id="USER-001",
        content="Great product! Love it!",
        created_at=datetime.now() - timedelta(hours=1),
    )


@pytest.fixture
def sample_question_comment():
    """示例问题评论"""
    return Comment(
        id="COMMENT-002",
        platform=SocialPlatform.FACEBOOK,
        post_id="POST-001",
        author="curious_user",
        author_id="USER-002",
        content="How much does this cost? Where can I buy it?",
        created_at=datetime.now() - timedelta(minutes=30),
    )


@pytest.fixture
def sample_complaint_comment():
    """示例投诉评论"""
    return Comment(
        id="COMMENT-003",
        platform=SocialPlatform.FACEBOOK,
        post_id="POST-001",
        author="unhappy_customer",
        author_id="USER-003",
        content="This is terrible! Not working at all. Very disappointed.",
        created_at=datetime.now() - timedelta(minutes=15),
    )


@pytest.fixture
def sample_spam_comment():
    """示例垃圾评论"""
    return Comment(
        id="COMMENT-004",
        platform=SocialPlatform.FACEBOOK,
        post_id="POST-001",
        author="spam_bot",
        author_id="USER-004",
        content="Buy now! Click here for free prize! http://spam.com",
        created_at=datetime.now(),
    )


# ============================================================================
# Comment Analyzer Tests
# ============================================================================


class TestCommentAnalyzer:
    """CommentAnalyzer 单元测试"""

    def test_analyzer_initialization(self, comment_analyzer):
        """测试分析器初始化"""
        assert comment_analyzer is not None
        assert comment_analyzer.llm is not None

    @pytest.mark.asyncio
    async def test_analyze_sentiment_positive(self, comment_analyzer):
        """测试分析正面情感"""
        content = "This is amazing! Love it so much! ❤️"
        
        sentiment = await comment_analyzer.analyze_sentiment(content)
        
        assert sentiment == CommentSentiment.POSITIVE

    @pytest.mark.asyncio
    async def test_analyze_sentiment_negative(self, comment_analyzer):
        """测试分析负面情感"""
        content = "This is terrible. Hate it. Worst ever! 👎"
        
        sentiment = await comment_analyzer.analyze_sentiment(content)
        
        assert sentiment == CommentSentiment.NEGATIVE

    @pytest.mark.asyncio
    async def test_analyze_sentiment_question(self, comment_analyzer):
        """测试分析问题"""
        content = "How does this work? Can you help me?"
        
        sentiment = await comment_analyzer.analyze_sentiment(content)
        
        assert sentiment == CommentSentiment.QUESTION

    @pytest.mark.asyncio
    async def test_analyze_sentiment_complaint(self, comment_analyzer):
        """测试分析投诉"""
        content = "I have a complaint. This is not working. Need refund."
        
        sentiment = await comment_analyzer.analyze_sentiment(content)
        
        assert sentiment == CommentSentiment.COMPLAINT

    @pytest.mark.asyncio
    async def test_analyze_sentiment_spam(self, comment_analyzer):
        """测试分析垃圾评论"""
        content = "Buy now! Click here for free! http://spam.com"
        
        sentiment = await comment_analyzer.analyze_sentiment(content)
        
        assert sentiment == CommentSentiment.SPAM

    @pytest.mark.asyncio
    async def test_analyze_sentiment_neutral(self, comment_analyzer):
        """测试分析中性情感"""
        content = "This is a regular comment."
        
        sentiment = await comment_analyzer.analyze_sentiment(content)
        
        assert sentiment == CommentSentiment.NEUTRAL

    @pytest.mark.asyncio
    async def test_analyze_sentiment_emoji_positive(self, comment_analyzer):
        """测试表情符号 - 正面"""
        content = "Thanks! 😊👍"
        
        sentiment = await comment_analyzer.analyze_sentiment(content)
        
        assert sentiment == CommentSentiment.POSITIVE

    @pytest.mark.asyncio
    async def test_analyze_sentiment_emoji_negative(self, comment_analyzer):
        """测试表情符号 - 负面"""
        content = "Not good 😡💔"
        
        sentiment = await comment_analyzer.analyze_sentiment(content)
        
        assert sentiment == CommentSentiment.NEGATIVE

    @pytest.mark.asyncio
    async def test_should_reply_spam(self, comment_analyzer, sample_spam_comment):
        """测试是否应该回复 - 垃圾评论"""
        sample_spam_comment.sentiment = CommentSentiment.SPAM
        
        should_reply = await comment_analyzer.should_reply(sample_spam_comment)
        
        assert should_reply is False

    @pytest.mark.asyncio
    async def test_should_reply_normal(self, comment_analyzer, sample_comment):
        """测试是否应该回复 - 正常评论"""
        sample_comment.sentiment = CommentSentiment.POSITIVE
        
        should_reply = await comment_analyzer.should_reply(sample_comment)
        
        assert should_reply is True

    @pytest.mark.asyncio
    async def test_should_reply_self(self, comment_analyzer):
        """测试是否应该回复 - 自己的评论"""
        comment = Comment(
            id="SELF-001",
            platform=SocialPlatform.FACEBOOK,
            post_id="POST-001",
            author="me",
            author_id="ME-001",
            content="Thanks!",
            created_at=datetime.now(),
        )
        
        should_reply = await comment_analyzer.should_reply(comment)
        
        assert should_reply is False

    @pytest.mark.asyncio
    async def test_calculate_priority_complaint(self, comment_analyzer, sample_complaint_comment):
        """测试计算优先级 - 投诉"""
        sample_complaint_comment.sentiment = CommentSentiment.COMPLAINT
        
        priority = await comment_analyzer.calculate_priority(sample_complaint_comment)
        
        assert priority >= 1
        assert priority <= 5

    @pytest.mark.asyncio
    async def test_calculate_priority_question(self, comment_analyzer, sample_question_comment):
        """测试计算优先级 - 问题"""
        sample_question_comment.sentiment = CommentSentiment.QUESTION
        
        priority = await comment_analyzer.calculate_priority(sample_question_comment)
        
        assert priority >= 1

    @pytest.mark.asyncio
    async def test_calculate_priority_recent(self, comment_analyzer):
        """测试计算优先级 - 最近的评论"""
        comment = Comment(
            id="RECENT-001",
            platform=SocialPlatform.FACEBOOK,
            post_id="POST-001",
            author="user",
            author_id="USER-001",
            content="Test",
            created_at=datetime.now(),
        )
        
        priority = await comment_analyzer.calculate_priority(comment)
        
        assert priority >= 1

    @pytest.mark.asyncio
    async def test_calculate_priority_verified(self, comment_analyzer):
        """测试计算优先级 - 认证用户"""
        comment = Comment(
            id="VERIFIED-001",
            platform=SocialPlatform.FACEBOOK,
            post_id="POST-001",
            author="verified_user",
            author_id="USER-001",
            content="Test",
            created_at=datetime.now() - timedelta(hours=1),
            metadata={"is_verified": True},
        )
        
        priority = await comment_analyzer.calculate_priority(comment)
        
        assert priority >= 1


# ============================================================================
# Reply Generator Tests
# ============================================================================


class TestReplyGenerator:
    """ReplyGenerator 单元测试"""

    def test_generator_initialization(self, reply_generator):
        """测试生成器初始化"""
        assert reply_generator is not None
        assert reply_generator.llm is not None

    @pytest.mark.asyncio
    async def test_generate_reply(self, reply_generator, sample_comment):
        """测试生成回复"""
        reply = await reply_generator.generate_reply(sample_comment)
        
        assert isinstance(reply, str)
        assert len(reply) > 0

    @pytest.mark.asyncio
    async def test_generate_reply_with_context(self, reply_generator, sample_comment):
        """测试带上下文生成回复"""
        context = "Customer is asking about pricing"
        
        reply = await reply_generator.generate_reply(
            sample_comment,
            context=context,
        )
        
        assert isinstance(reply, str)

    @pytest.mark.asyncio
    async def test_generate_reply_with_brand_voice(self, reply_generator, sample_comment):
        """测试带品牌语调生成回复"""
        reply = await reply_generator.generate_reply(
            sample_comment,
            brand_voice="casual and friendly",
        )
        
        assert isinstance(reply, str)

    @pytest.mark.asyncio
    async def test_generate_question_reply(self, reply_generator, sample_question_comment):
        """测试生成问题回复"""
        reply = await reply_generator.generate_question_reply(sample_question_comment)
        
        assert isinstance(reply, str)
        assert len(reply) > 0

    @pytest.mark.asyncio
    async def test_generate_question_reply_with_faq(self, reply_generator, sample_question_comment):
        """测试使用 FAQ 生成问题回复"""
        faq_data = {
            "how much": "Our product costs $99.",
            "where to buy": "You can buy from our website.",
        }
        
        reply = await reply_generator.generate_question_reply(
            sample_question_comment,
            faq_data=faq_data,
        )
        
        assert isinstance(reply, str)

    @pytest.mark.asyncio
    async def test_generate_complaint_reply(self, reply_generator, sample_complaint_comment):
        """测试生成投诉回复"""
        reply = await reply_generator.generate_complaint_reply(sample_complaint_comment)
        
        assert isinstance(reply, str)
        assert len(reply) > 0

    @pytest.mark.asyncio
    async def test_generate_complaint_reply_with_support(self, reply_generator, sample_complaint_comment):
        """测试带支持联系方式生成投诉回复"""
        reply = await reply_generator.generate_complaint_reply(
            sample_complaint_comment,
            support_contact="Contact us at support@example.com",
        )
        
        assert isinstance(reply, str)


# ============================================================================
# Community Monitor Tests
# ============================================================================


class TestCommunityMonitor:
    """CommunityMonitor 单元测试"""

    def test_monitor_initialization(self, community_monitor):
        """测试监控器初始化"""
        assert community_monitor is not None
        assert community_monitor.analyzer is not None
        assert community_monitor.reply_generator is not None
        assert len(community_monitor._monitored_posts) == 0

    @pytest.mark.asyncio
    async def test_start_monitoring(self, community_monitor):
        """测试开始监控"""
        await community_monitor.start_monitoring(
            SocialPlatform.FACEBOOK,
            "POST-001",
            check_interval=300,
        )
        
        key = "facebook:POST-001"
        assert key in community_monitor._monitored_posts
        assert community_monitor._monitored_posts[key]["active"] is True

    @pytest.mark.asyncio
    async def test_stop_monitoring(self, community_monitor):
        """测试停止监控"""
        await community_monitor.start_monitoring(
            SocialPlatform.FACEBOOK,
            "POST-001",
        )
        
        await community_monitor.stop_monitoring(
            SocialPlatform.FACEBOOK,
            "POST-001",
        )
        
        key = "facebook:POST-001"
        assert community_monitor._monitored_posts[key]["active"] is False

    def test_add_auto_reply_rule(self, community_monitor):
        """测试添加自动回复规则"""
        rule = AutoReplyRule(
            id="RULE-001",
            platform=SocialPlatform.FACEBOOK,
            keywords=["price", "cost"],
            sentiment=CommentSentiment.QUESTION,
            response_template="Our price is ${price}.",
            auto_send=False,
            priority=1,
        )
        
        community_monitor.add_auto_reply_rule(rule)
        
        assert len(community_monitor._auto_reply_rules) == 1

    def test_add_reply_template(self, community_monitor):
        """测试添加回复模板"""
        template = ReplyTemplate(
            id="TEMPLATE-001",
            name="Thank You",
            platform=SocialPlatform.FACEBOOK,
            trigger_keywords=["thanks", "thank you"],
            template="You're welcome!",
            priority=1,
        )
        
        community_monitor.add_reply_template(template)
        
        assert len(community_monitor._reply_templates) == 1

    def test_get_pending_comments_empty(self, community_monitor):
        """测试获取待处理评论 - 空"""
        pending = community_monitor.get_pending_comments()
        
        assert len(pending) == 0

    def test_get_metrics(self, community_monitor):
        """测试获取指标"""
        metrics = community_monitor.get_metrics()
        
        assert isinstance(metrics, CommunityMetrics)
        assert metrics.total_comments == 0
        assert metrics.total_replies == 0


# ============================================================================
# Community Automation Tests
# ============================================================================


class TestCommunityAutomation:
    """CommunityAutomation 单元测试"""

    def test_automation_initialization(self, community_automation):
        """测试自动化初始化"""
        assert community_automation is not None
        assert community_automation.monitor is not None
        assert community_automation._running is False

    def test_stop_automation(self, community_automation):
        """测试停止自动化"""
        community_automation._running = True
        community_automation.stop()
        
        assert community_automation._running is False

    def test_get_pending_replies(self, community_automation):
        """测试获取待回复"""
        pending = community_automation.get_pending_replies()
        
        assert isinstance(pending, list)


# ============================================================================
# Comment Model Tests
# ============================================================================


class TestComment:
    """Comment 模型单元测试"""

    def test_comment_creation(self, sample_comment):
        """测试评论创建"""
        assert sample_comment.id == "COMMENT-001"
        assert sample_comment.author == "test_user"
        assert sample_comment.content == "Great product! Love it!"
        assert sample_comment.needs_reply is True
        assert sample_comment.replied is False

    def test_comment_with_sentiment(self):
        """测试带情感的评论"""
        comment = Comment(
            id="COMMENT-005",
            platform=SocialPlatform.FACEBOOK,
            post_id="POST-001",
            author="user",
            author_id="USER-005",
            content="Love this!",
            created_at=datetime.now(),
            sentiment=CommentSentiment.POSITIVE,
        )
        
        assert comment.sentiment == CommentSentiment.POSITIVE

    def test_comment_with_priority(self):
        """测试带优先级的评论"""
        comment = Comment(
            id="COMMENT-006",
            platform=SocialPlatform.FACEBOOK,
            post_id="POST-001",
            author="vip_user",
            author_id="USER-006",
            content="Important!",
            created_at=datetime.now(),
            priority=5,
        )
        
        assert comment.priority == 5

    def test_comment_with_metadata(self):
        """测试带元数据的评论"""
        comment = Comment(
            id="COMMENT-007",
            platform=SocialPlatform.FACEBOOK,
            post_id="POST-001",
            author="user",
            author_id="USER-007",
            content="Test",
            created_at=datetime.now(),
            metadata={"follower_count": 10000, "is_verified": True},
        )
        
        assert comment.metadata["follower_count"] == 10000
        assert comment.metadata["is_verified"] is True


class TestCommentSentiment:
    """CommentSentiment 单元测试"""

    def test_sentiment_enum(self):
        """测试情感枚举"""
        assert CommentSentiment.POSITIVE.value == "positive"
        assert CommentSentiment.NEGATIVE.value == "negative"
        assert CommentSentiment.NEUTRAL.value == "neutral"
        assert CommentSentiment.QUESTION.value == "question"
        assert CommentSentiment.COMPLAINT.value == "complaint"
        assert CommentSentiment.SPAM.value == "spam"


class TestReplyType:
    """ReplyType 单元测试"""

    def test_reply_type_enum(self):
        """测试回复类型枚举"""
        assert ReplyType.AUTO.value == "auto"
        assert ReplyType.SUGGESTED.value == "suggested"
        assert ReplyType.MANUAL.value == "manual"
        assert ReplyType.TEMPLATE.value == "template"


class TestCommunityMetrics:
    """CommunityMetrics 单元测试"""

    def test_metrics_creation(self):
        """测试指标创建"""
        metrics = CommunityMetrics(
            platform=SocialPlatform.FACEBOOK,
            period="last_7_days",
            total_comments=100,
            total_replies=80,
            positive_sentiment=60,
            negative_sentiment=20,
            neutral_sentiment=20,
        )
        
        assert metrics.platform == SocialPlatform.FACEBOOK
        assert metrics.period == "last_7_days"
        assert metrics.total_comments == 100
        assert metrics.total_replies == 80


class TestAutoReplyRule:
    """AutoReplyRule 单元测试"""

    def test_rule_creation(self):
        """测试规则创建"""
        rule = AutoReplyRule(
            id="RULE-001",
            platform=SocialPlatform.FACEBOOK,
            keywords=["price", "cost"],
            sentiment=CommentSentiment.QUESTION,
            response_template="Our price is $99.",
            auto_send=True,
            require_approval=False,
            priority=1,
        )
        
        assert rule.id == "RULE-001"
        assert rule.platform == SocialPlatform.FACEBOOK
        assert rule.auto_send is True


class TestReplyTemplate:
    """ReplyTemplate 单元测试"""

    def test_template_creation(self):
        """测试模板创建"""
        template = ReplyTemplate(
            id="TEMPLATE-001",
            name="Thank You",
            platform=SocialPlatform.FACEBOOK,
            trigger_keywords=["thanks", "thank you"],
            template="You're welcome! 😊",
            priority=1,
            enabled=True,
        )
        
        assert template.id == "TEMPLATE-001"
        assert template.name == "Thank You"
        assert template.enabled is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
