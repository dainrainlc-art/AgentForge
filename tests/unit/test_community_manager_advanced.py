"""
Community Manager 补充测试 - 提升覆盖率到 80%
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from agentforge.community.community_manager import (
    CommentAnalyzer,
    ReplyGenerator,
    CommunityMonitor,
    Comment,
    CommentSentiment,
    ReplyType,
    ReplyTemplate,
    AutoReplyRule,
    CommunityMetrics,
)
from integrations.external.social_client import SocialPlatform


class TestCommentAnalyzerAdvanced:
    """CommentAnalyzer 高级测试"""
    
    @pytest.fixture
    def analyzer(self):
        return CommentAnalyzer()
    
    @pytest.mark.asyncio
    async def test_analyze_sentiment_positive_with_emojis(self, analyzer):
        """测试积极情绪识别（带表情）"""
        content = "This is amazing! 😍 Love it! ❤️"
        result = await analyzer.analyze_sentiment(content)
        assert result == CommentSentiment.POSITIVE
    
    @pytest.mark.asyncio
    async def test_analyze_sentiment_negative_with_emojis(self, analyzer):
        """测试消极情绪识别（带表情）"""
        content = "This is terrible 😡 Worst experience ever 👎"
        result = await analyzer.analyze_sentiment(content)
        assert result == CommentSentiment.NEGATIVE
    
    @pytest.mark.asyncio
    async def test_analyze_sentiment_question_mark(self, analyzer):
        """测试问句识别"""
        content = "How do I use this product?"
        result = await analyzer.analyze_sentiment(content)
        assert result == CommentSentiment.QUESTION
    
    @pytest.mark.asyncio
    async def test_analyze_sentiment_question_words(self, analyzer):
        """测试疑问词识别"""
        content = "What is the price and when will it be available"
        result = await analyzer.analyze_sentiment(content)
        assert result == CommentSentiment.QUESTION
    
    @pytest.mark.asyncio
    async def test_analyze_sentiment_complaint(self, analyzer):
        """测试投诉识别"""
        content = "I have a complaint. The product is not working properly."
        result = await analyzer.analyze_sentiment(content)
        assert result == CommentSentiment.COMPLAINT
    
    @pytest.mark.asyncio
    async def test_analyze_sentiment_spam_url(self, analyzer):
        """测试垃圾信息识别（URL）"""
        content = "Check out my profile http://spam.com"
        result = await analyzer.analyze_sentiment(content)
        assert result == CommentSentiment.SPAM
    
    @pytest.mark.asyncio
    async def test_analyze_sentiment_spam_promotion(self, analyzer):
        """测试垃圾信息识别（推广）"""
        content = "Buy now! Free winner! Click here to claim $"
        result = await analyzer.analyze_sentiment(content)
        assert result == CommentSentiment.SPAM
    
    @pytest.mark.asyncio
    async def test_analyze_sentiment_neutral(self, analyzer):
        """测试中性情绪识别"""
        content = "The package arrived today. It looks okay."
        result = await analyzer.analyze_sentiment(content)
        assert result == CommentSentiment.NEUTRAL
    
    @pytest.mark.asyncio
    async def test_should_reply_spam(self, analyzer):
        """测试垃圾信息不回复"""
        comment = Comment(
            id="spam_123",
            platform=SocialPlatform.FACEBOOK,
            post_id="post_1",
            author="spammer",
            author_id="user_123",
            content="Buy now! Click here!",
            created_at=datetime.now(),
            sentiment=CommentSentiment.SPAM
        )
        
        result = await analyzer.should_reply(comment)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_should_reply_self(self, analyzer):
        """测试自己的评论不回复"""
        comment = Comment(
            id="self_123",
            platform=SocialPlatform.FACEBOOK,
            post_id="post_1",
            author="me",
            author_id="user_123",
            content="Thanks everyone!",
            created_at=datetime.now(),
            sentiment=CommentSentiment.POSITIVE
        )
        
        result = await analyzer.should_reply(comment)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_should_reply_normal(self, analyzer):
        """测试正常评论需要回复"""
        comment = Comment(
            id="normal_123",
            platform=SocialPlatform.FACEBOOK,
            post_id="post_1",
            author="customer",
            author_id="user_123",
            content="Great product!",
            created_at=datetime.now(),
            sentiment=CommentSentiment.POSITIVE
        )
        
        result = await analyzer.should_reply(comment)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_calculate_priority_complaint(self, analyzer):
        """测试投诉评论优先级"""
        comment = Comment(
            id="complaint_123",
            platform=SocialPlatform.FACEBOOK,
            post_id="post_1",
            author="customer",
            author_id="user_123",
            content="I have a problem with my order",
            created_at=datetime.now(),
            sentiment=CommentSentiment.COMPLAINT
        )
        
        result = await analyzer.calculate_priority(comment)
        assert result >= 4  # 基础 1 + 投诉 3
    
    @pytest.mark.asyncio
    async def test_calculate_priority_question(self, analyzer):
        """测试问题评论优先级"""
        comment = Comment(
            id="question_123",
            platform=SocialPlatform.FACEBOOK,
            post_id="post_1",
            author="customer",
            author_id="user_123",
            content="How does this work?",
            created_at=datetime.now(),
            sentiment=CommentSentiment.QUESTION
        )
        
        result = await analyzer.calculate_priority(comment)
        assert result >= 3  # 基础 1 + 问题 2
    
    @pytest.mark.asyncio
    async def test_calculate_priority_recent(self, analyzer):
        """测试最新评论优先级"""
        comment = Comment(
            id="recent_123",
            platform=SocialPlatform.FACEBOOK,
            post_id="post_1",
            author="customer",
            author_id="user_123",
            content="Just received it!",
            created_at=datetime.now(),
            sentiment=CommentSentiment.POSITIVE
        )
        
        result = await analyzer.calculate_priority(comment)
        assert result >= 3  # 基础 1 + 1 小时内 2
    
    @pytest.mark.asyncio
    async def test_calculate_priority_old_comment(self, analyzer):
        """测试旧评论优先级"""
        old_time = datetime.now() - timedelta(hours=12)
        comment = Comment(
            id="old_123",
            platform=SocialPlatform.FACEBOOK,
            post_id="post_1",
            author="customer",
            author_id="user_123",
            content="Received last week",
            created_at=old_time,
            sentiment=CommentSentiment.POSITIVE
        )
        
        result = await analyzer.calculate_priority(comment)
        assert result == 1  # 基础优先级


class TestReplyGeneratorAdvanced:
    """ReplyGenerator 高级测试"""
    
    @pytest.fixture
    def reply_generator(self):
        return ReplyGenerator()
    
    @pytest.mark.asyncio
    async def test_generate_question_reply_with_faq(self, reply_generator):
        """测试使用 FAQ 生成问题回复"""
        comment = Comment(
            id="q_123",
            platform=SocialPlatform.FACEBOOK,
            post_id="post_1",
            author="customer",
            author_id="user_123",
            content="What is the shipping time?",
            created_at=datetime.now(),
            sentiment=CommentSentiment.QUESTION
        )
        
        faq_data = {
            "what is the shipping time": "Shipping takes 3-5 business days.",
            "how to return": "You can return within 30 days."
        }
        
        result = await reply_generator.generate_question_reply(comment, faq_data)
        assert "Shipping takes 3-5 business days" in result
    
    @pytest.mark.asyncio
    async def test_generate_question_reply_without_faq(self, reply_generator):
        """测试没有 FAQ 时生成问题回复"""
        comment = Comment(
            id="q_456",
            platform=SocialPlatform.FACEBOOK,
            post_id="post_1",
            author="customer",
            author_id="user_123",
            content="Do you ship internationally?",
            created_at=datetime.now(),
            sentiment=CommentSentiment.QUESTION
        )
        
        with patch.object(reply_generator, 'generate_reply') as mock_generate:
            mock_generate.return_value = "Yes, we ship internationally!"
            result = await reply_generator.generate_question_reply(comment)
            mock_generate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_complaint_reply(self, reply_generator):
        """测试生成投诉回复"""
        comment = Comment(
            id="complaint_456",
            platform=SocialPlatform.FACEBOOK,
            post_id="post_1",
            author="unhappy_customer",
            author_id="user_456",
            content="My order arrived damaged!",
            created_at=datetime.now(),
            sentiment=CommentSentiment.COMPLAINT
        )
        
        with patch.object(reply_generator.llm, 'chat_with_failover') as mock_llm:
            mock_llm.return_value = "We apologize for the inconvenience. DM us for support."
            result = await reply_generator.generate_complaint_reply(comment)
            assert "apologize" in result.lower() or "support" in result.lower()
            mock_llm.assert_called_once()


class TestCommunityMonitorAdvanced:
    """CommunityMonitor 高级测试"""
    
    @pytest.fixture
    def monitor(self):
        return CommunityMonitor()
    
    @pytest.mark.asyncio
    async def test_start_monitoring(self, monitor):
        """测试开始监控"""
        await monitor.start_monitoring(
            SocialPlatform.FACEBOOK,
            "post_123",
            check_interval=600
        )
        
        key = "facebook:post_123"
        assert key in monitor._monitored_posts
        assert monitor._monitored_posts[key]["active"] is True
        assert monitor._monitored_posts[key]["check_interval"] == 600
    
    @pytest.mark.asyncio
    async def test_stop_monitoring(self, monitor):
        """测试停止监控"""
        await monitor.start_monitoring(SocialPlatform.FACEBOOK, "post_456")
        key = "facebook:post_456"
        assert key in monitor._monitored_posts
        
        await monitor.stop_monitoring(SocialPlatform.FACEBOOK, "post_456")
        assert monitor._monitored_posts[key]["active"] is False
    
    @pytest.mark.asyncio
    async def test_stop_monitoring_not_exists(self, monitor):
        """测试停止不存在的监控"""
        # 不应该抛出异常
        await monitor.stop_monitoring(SocialPlatform.FACEBOOK, "nonexistent")
    
    @pytest.mark.asyncio
    async def test_check_comments_inactive(self, monitor):
        """测试非活跃监控的检查"""
        await monitor.start_monitoring(SocialPlatform.FACEBOOK, "post_789")
        key = "facebook:post_789"
        monitor._monitored_posts[key]["active"] = False
        
        result = await monitor.check_comments()
        assert result == []
    
    @pytest.mark.asyncio
    async def test_check_comments_with_error(self, monitor):
        """测试检查评论时出错"""
        await monitor.start_monitoring(SocialPlatform.FACEBOOK, "post_error")
        
        with patch.object(monitor, '_fetch_comments', side_effect=Exception("API Error")):
            result = await monitor.check_comments()
            # 应该返回空列表而不是抛出异常
            assert isinstance(result, list)
    
    def test_add_auto_reply_rule(self, monitor):
        """测试添加自动回复规则"""
        rule = AutoReplyRule(
            id="rule_1",
            platform=SocialPlatform.FACEBOOK,
            keywords=["hello", "hi"],
            response_template="Hello {author}!",
            auto_send=False,
            priority=2
        )
        
        monitor.add_auto_reply_rule(rule)
        assert len(monitor._auto_reply_rules) == 1
        assert monitor._auto_reply_rules[0].id == "rule_1"
    
    def test_add_auto_reply_rule_priority_sort(self, monitor):
        """测试自动回复规则按优先级排序"""
        rule1 = AutoReplyRule(
            id="rule_low",
            platform=SocialPlatform.FACEBOOK,
            keywords=["test"],
            response_template="Test",
            priority=1
        )
        
        rule2 = AutoReplyRule(
            id="rule_high",
            platform=SocialPlatform.FACEBOOK,
            keywords=["test"],
            response_template="Test",
            priority=5
        )
        
        monitor.add_auto_reply_rule(rule1)
        monitor.add_auto_reply_rule(rule2)
        
        # 高优先级应该排在前面
        assert monitor._auto_reply_rules[0].id == "rule_high"
        assert monitor._auto_reply_rules[1].id == "rule_low"
    
    def test_add_reply_template(self, monitor):
        """测试添加回复模板"""
        template = ReplyTemplate(
            id="template_1",
            name="Welcome",
            platform=SocialPlatform.FACEBOOK,
            trigger_keywords=["welcome"],
            template="Welcome to our page!"
        )
        
        monitor.add_reply_template(template)
        assert len(monitor._reply_templates) == 1
    
    def test_get_pending_comments(self, monitor):
        """测试获取待处理评论"""
        comment1 = Comment(
            id="pending_1",
            platform=SocialPlatform.FACEBOOK,
            post_id="post_1",
            author="user1",
            author_id="u1",
            content="Question?",
            created_at=datetime.now(),
            replied=False,
            needs_reply=True
        )
        
        comment2 = Comment(
            id="replied_1",
            platform=SocialPlatform.FACEBOOK,
            post_id="post_1",
            author="user2",
            author_id="u2",
            content="Thanks!",
            created_at=datetime.now(),
            replied=True,
            needs_reply=False
        )
        
        monitor._comment_queue = [comment1, comment2]
        
        pending = monitor.get_pending_comments()
        assert len(pending) == 1
        assert pending[0].id == "pending_1"
    
    def test_get_metrics_default(self, monitor):
        """测试获取默认指标"""
        metrics = monitor.get_metrics()
        assert isinstance(metrics, CommunityMetrics)
        assert metrics.total_comments == 0
        assert metrics.total_replies == 0
    
    def test_get_metrics_with_data(self, monitor):
        """测试获取有数据的指标"""
        positive_comment = Comment(
            id="pos_1",
            platform=SocialPlatform.FACEBOOK,
            post_id="post_1",
            author="user1",
            author_id="u1",
            content="Great!",
            created_at=datetime.now(),
            sentiment=CommentSentiment.POSITIVE,
            replied=True
        )
        
        question_comment = Comment(
            id="q_1",
            platform=SocialPlatform.FACEBOOK,
            post_id="post_1",
            author="user2",
            author_id="u2",
            content="How?",
            created_at=datetime.now(),
            sentiment=CommentSentiment.QUESTION,
            replied=False
        )
        
        monitor._comment_queue = [positive_comment, question_comment]
        
        metrics = monitor.get_metrics()
        assert metrics.total_comments == 2
        assert metrics.positive_sentiment == 1
        assert metrics.questions_answered == 0  # 未回复
    
    @pytest.mark.asyncio
    async def test_process_comment_auto_reply_match(self, monitor):
        """测试处理评论 - 匹配自动回复规则"""
        rule = AutoReplyRule(
            id="auto_rule_1",
            platform=SocialPlatform.FACEBOOK,
            keywords=["price"],
            response_template="The price is $99.",
            auto_send=False,
            priority=1
        )
        monitor.add_auto_reply_rule(rule)
        
        comment = Comment(
            id="price_q",
            platform=SocialPlatform.FACEBOOK,
            post_id="post_1",
            author="customer",
            author_id="c1",
            content="What is the price?",
            created_at=datetime.now(),
            sentiment=CommentSentiment.QUESTION
        )
        
        with patch.object(monitor.reply_generator, 'generate_reply') as mock_generate:
            mock_generate.return_value = "The price is $99."
            result = await monitor.process_comment(comment)
            assert result == "The price is $99."
    
    @pytest.mark.asyncio
    async def test_process_comment_no_match(self, monitor):
        """测试处理评论 - 无匹配规则"""
        comment = Comment(
            id="general_1",
            platform=SocialPlatform.FACEBOOK,
            post_id="post_1",
            author="customer",
            author_id="c1",
            content="Nice post!",
            created_at=datetime.now(),
            sentiment=CommentSentiment.POSITIVE
        )
        
        with patch.object(monitor.reply_generator, 'generate_reply') as mock_generate:
            mock_generate.return_value = "Thank you!"
            result = await monitor.process_comment(comment)
            mock_generate.assert_called_once()
            assert result == "Thank you!"


class TestDataModels:
    """数据模型测试"""
    
    def test_comment_creation(self):
        """测试评论对象创建"""
        comment = Comment(
            id="test_123",
            platform=SocialPlatform.FACEBOOK,
            post_id="post_1",
            author="Test User",
            author_id="user_123",
            content="This is a test comment",
            created_at=datetime.now()
        )
        
        assert comment.id == "test_123"
        assert comment.platform == SocialPlatform.FACEBOOK
        assert comment.needs_reply is True
        assert comment.replied is False
        assert comment.reply_id is None
    
    def test_reply_template_creation(self):
        """测试回复模板创建"""
        template = ReplyTemplate(
            id="template_1",
            name="Welcome Message",
            platform=SocialPlatform.FACEBOOK,
            trigger_keywords=["welcome", "hello"],
            template="Welcome to our page, {author}!"
        )
        
        assert template.id == "template_1"
        assert template.enabled is True
        assert template.sentiment_filter is None
        assert len(template.trigger_keywords) == 2
    
    def test_auto_reply_rule_creation(self):
        """测试自动回复规则创建"""
        rule = AutoReplyRule(
            id="rule_1",
            platform=SocialPlatform.INSTAGRAM,
            keywords=["question", "help"],
            sentiment=CommentSentiment.QUESTION,
            response_template="I'd be happy to help!",
            auto_send=True,
            require_approval=False,
            priority=3
        )
        
        assert rule.id == "rule_1"
        assert rule.auto_send is True
        assert rule.require_approval is False
        assert rule.enabled is True
    
    def test_community_metrics_creation(self):
        """测试社区指标创建"""
        metrics = CommunityMetrics(
            platform=SocialPlatform.FACEBOOK,
            period="2024-01",
            total_comments=100,
            total_replies=80,
            avg_response_time=2.5,
            positive_sentiment=60,
            negative_sentiment=10,
            neutral_sentiment=30,
            questions_answered=15,
            complaints_resolved=8,
            spam_detected=5
        )
        
        assert metrics.total_comments == 100
        assert metrics.total_replies == 80
        assert metrics.avg_response_time == 2.5
        assert metrics.positive_sentiment == 60


class TestReplyType:
    """ReplyType 枚举测试"""
    
    def test_reply_type_values(self):
        """测试回复类型枚举值"""
        assert ReplyType.AUTO.value == "auto"
        assert ReplyType.SUGGESTED.value == "suggested"
        assert ReplyType.MANUAL.value == "manual"
        assert ReplyType.TEMPLATE.value == "template"


class TestCommentSentiment:
    """CommentSentiment 枚举测试"""
    
    def test_sentiment_values(self):
        """测试情绪枚举值"""
        assert CommentSentiment.POSITIVE.value == "positive"
        assert CommentSentiment.NEGATIVE.value == "negative"
        assert CommentSentiment.NEUTRAL.value == "neutral"
        assert CommentSentiment.QUESTION.value == "question"
        assert CommentSentiment.COMPLAINT.value == "complaint"
        assert CommentSentiment.SPAM.value == "spam"
