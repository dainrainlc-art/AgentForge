"""
AgentForge Community Management Module
Auto-reply and community monitoring functionality
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum
from pydantic import BaseModel, Field
import re
import asyncio
from loguru import logger

from agentforge.llm.model_router import ModelRouter
from integrations.external.social_client import (
    SocialPlatform,
    SocialMediaClient,
)


class ReplyType(str, Enum):
    AUTO = "auto"
    SUGGESTED = "suggested"
    MANUAL = "manual"
    TEMPLATE = "template"


class CommentSentiment(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    QUESTION = "question"
    COMPLAINT = "complaint"
    SPAM = "spam"


class Comment(BaseModel):
    id: str
    platform: SocialPlatform
    post_id: str
    author: str
    author_id: str
    content: str
    created_at: datetime
    sentiment: Optional[CommentSentiment] = None
    needs_reply: bool = True
    priority: int = 1
    replied: bool = False
    reply_id: Optional[str] = None
    reply_content: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ReplyTemplate(BaseModel):
    id: str
    name: str
    platform: SocialPlatform
    trigger_keywords: List[str]
    sentiment_filter: Optional[CommentSentiment] = None
    template: str
    priority: int = 1
    enabled: bool = True


class AutoReplyRule(BaseModel):
    id: str
    platform: SocialPlatform
    keywords: List[str]
    sentiment: Optional[CommentSentiment] = None
    response_template: str
    auto_send: bool = False
    require_approval: bool = True
    priority: int = 1
    enabled: bool = True


class CommunityMetrics(BaseModel):
    platform: SocialPlatform
    period: str
    total_comments: int = 0
    total_replies: int = 0
    avg_response_time: float = 0.0
    positive_sentiment: int = 0
    negative_sentiment: int = 0
    neutral_sentiment: int = 0
    questions_answered: int = 0
    complaints_resolved: int = 0
    spam_detected: int = 0


class CommentAnalyzer:
    def __init__(self):
        self.llm = ModelRouter()
    
    async def analyze_sentiment(self, content: str) -> CommentSentiment:
        content_lower = content.lower()
        
        positive_patterns = [
            r'\b(great|awesome|amazing|excellent|love|perfect|wonderful|fantastic|best|good|nice)\b',
            r'❤️|💕|😍|🥰|👍|👏|🎉',
        ]
        
        negative_patterns = [
            r'\b(bad|terrible|awful|hate|worst|horrible|disappointing|poor|scam|fraud)\b',
            r'😡|😤|👎|💔|😠',
        ]
        
        question_patterns = [
            r'\?',
            r'\b(how|what|when|where|why|who|can you|could you|would you)\b',
        ]
        
        complaint_patterns = [
            r'\b(complaint|problem|issue|not working|broken|error|bug|fix|refund)\b',
            r'\b(disappointed|unhappy|unsatisfied)\b',
        ]
        
        spam_patterns = [
            r'\b(buy now|click here|free|winner|congratulations|follow me|check my)\b',
            r'http[s]?://',
            r'\$[0-9]+',
        ]
        
        for pattern in spam_patterns:
            if re.search(pattern, content_lower):
                return CommentSentiment.SPAM
        
        for pattern in complaint_patterns:
            if re.search(pattern, content_lower):
                return CommentSentiment.COMPLAINT
        
        for pattern in question_patterns:
            if re.search(pattern, content_lower):
                return CommentSentiment.QUESTION
        
        for pattern in negative_patterns:
            if re.search(pattern, content_lower):
                return CommentSentiment.NEGATIVE
        
        for pattern in positive_patterns:
            if re.search(pattern, content_lower):
                return CommentSentiment.POSITIVE
        
        return CommentSentiment.NEUTRAL
    
    async def should_reply(self, comment: Comment) -> bool:
        if comment.sentiment == CommentSentiment.SPAM:
            return False
        
        if comment.author.lower() in ['me', 'self', comment.metadata.get('page_name', '').lower()]:
            return False
        
        return True
    
    async def calculate_priority(self, comment: Comment) -> int:
        priority = 1
        
        if comment.sentiment == CommentSentiment.COMPLAINT:
            priority += 3
        elif comment.sentiment == CommentSentiment.QUESTION:
            priority += 2
        elif comment.sentiment == CommentSentiment.NEGATIVE:
            priority += 2
        
        hours_old = (datetime.now() - comment.created_at).total_seconds() / 3600
        if hours_old < 1:
            priority += 2
        elif hours_old < 6:
            priority += 1
        
        if comment.metadata.get('is_verified', False):
            priority += 1
        
        if comment.metadata.get('follower_count', 0) > 10000:
            priority += 1
        
        return min(priority, 5)


class ReplyGenerator:
    def __init__(self):
        self.llm = ModelRouter()
    
    async def generate_reply(
        self,
        comment: Comment,
        context: Optional[str] = None,
        brand_voice: str = "professional and friendly"
    ) -> str:
        prompt = f"""Generate a reply to this social media comment.

Comment: "{comment.content}"
Author: {comment.author}
Platform: {comment.platform.value}
Sentiment: {comment.sentiment.value if comment.sentiment else 'unknown'}
Brand Voice: {brand_voice}

{"Additional context: " + context if context else ""}

Guidelines:
- Be {brand_voice}
- Keep it concise (under 280 characters for Twitter, 500 for others)
- Address the specific content of the comment
- If it's a question, provide a helpful answer
- If it's a complaint, acknowledge and offer to help
- If it's positive, express gratitude
- Do not use excessive emojis

Reply:"""

        response = await self.llm.chat_with_failover(
            message=prompt,
            task_type="creative"
        )
        return response.strip()
    
    async def generate_question_reply(
        self,
        comment: Comment,
        faq_data: Optional[Dict[str, str]] = None
    ) -> str:
        if faq_data:
            for question, answer in faq_data.items():
                if any(kw in comment.content.lower() for kw in question.lower().split()):
                    return answer
        
        return await self.generate_reply(comment, context="This is a question that needs a helpful answer.")
    
    async def generate_complaint_reply(
        self,
        comment: Comment,
        support_contact: str = "DM us for support"
    ) -> str:
        prompt = f"""Generate a professional reply to a customer complaint.

Complaint: "{comment.content}"
Author: {comment.author}
Platform: {comment.platform.value}

Guidelines:
- Acknowledge their frustration
- Apologize for the inconvenience
- Offer a solution or next steps
- Provide contact information: {support_contact}
- Keep it professional and empathetic

Reply:"""

        response = await self.llm.chat_with_failover(
            message=prompt,
            task_type="creative"
        )
        return response.strip()


class CommunityMonitor:
    def __init__(self):
        self.social_client = SocialMediaClient()
        self.analyzer = CommentAnalyzer()
        self.reply_generator = ReplyGenerator()
        
        self._monitored_posts: Dict[str, Dict[str, Any]] = {}
        self._auto_reply_rules: List[AutoReplyRule] = []
        self._reply_templates: List[ReplyTemplate] = []
        self._comment_queue: List[Comment] = []
    
    async def start_monitoring(
        self,
        platform: SocialPlatform,
        post_id: str,
        check_interval: int = 300
    ) -> None:
        key = f"{platform.value}:{post_id}"
        
        self._monitored_posts[key] = {
            "platform": platform,
            "post_id": post_id,
            "last_check": datetime.now(),
            "check_interval": check_interval,
            "active": True,
        }
        
        logger.info(f"Started monitoring {key}")
    
    async def stop_monitoring(self, platform: SocialPlatform, post_id: str) -> None:
        key = f"{platform.value}:{post_id}"
        
        if key in self._monitored_posts:
            self._monitored_posts[key]["active"] = False
            logger.info(f"Stopped monitoring {key}")
    
    async def check_comments(self) -> List[Comment]:
        new_comments = []
        
        for key, config in self._monitored_posts.items():
            if not config["active"]:
                continue
            
            platform = config["platform"]
            post_id = config["post_id"]
            
            try:
                comments_data = await self._fetch_comments(platform, post_id)
                
                for data in comments_data:
                    comment = Comment(
                        id=data.get("id", ""),
                        platform=platform,
                        post_id=post_id,
                        author=data.get("from", {}).get("name", "Unknown"),
                        author_id=data.get("from", {}).get("id", ""),
                        content=data.get("message") or data.get("text", ""),
                        created_at=datetime.fromisoformat(
                            data.get("created_time", datetime.now().isoformat()).replace("Z", "+00:00")
                        ),
                        metadata=data,
                    )
                    
                    comment.sentiment = await self.analyzer.analyze_sentiment(comment.content)
                    comment.needs_reply = await self.analyzer.should_reply(comment)
                    comment.priority = await self.analyzer.calculate_priority(comment)
                    
                    new_comments.append(comment)
                
                config["last_check"] = datetime.now()
                
            except Exception as e:
                logger.error(f"Error checking comments for {key}: {e}")
        
        self._comment_queue.extend(new_comments)
        self._comment_queue.sort(key=lambda c: c.priority, reverse=True)
        
        return new_comments
    
    async def _fetch_comments(
        self,
        platform: SocialPlatform,
        post_id: str
    ) -> List[Dict[str, Any]]:
        if platform == SocialPlatform.FACEBOOK:
            return await self.social_client.facebook.get_comments(post_id)
        elif platform == SocialPlatform.INSTAGRAM:
            return await self.social_client.instagram.get_comments(post_id)
        return []
    
    def add_auto_reply_rule(self, rule: AutoReplyRule) -> None:
        self._auto_reply_rules.append(rule)
        self._auto_reply_rules.sort(key=lambda r: r.priority, reverse=True)
    
    def add_reply_template(self, template: ReplyTemplate) -> None:
        self._reply_templates.append(template)
    
    async def process_comment(self, comment: Comment) -> Optional[str]:
        for rule in self._auto_reply_rules:
            if not rule.enabled:
                continue
            
            if rule.platform != comment.platform:
                continue
            
            if rule.sentiment and rule.sentiment != comment.sentiment:
                continue
            
            keyword_match = any(
                kw.lower() in comment.content.lower()
                for kw in rule.keywords
            )
            
            if keyword_match:
                reply = rule.response_template.format(
                    author=comment.author,
                    platform=comment.platform.value,
                )
                
                if rule.auto_send:
                    success = await self._send_reply(comment, reply)
                    if success:
                        comment.replied = True
                        comment.reply_content = reply
                        return reply
                
                return reply
        
        return await self.reply_generator.generate_reply(comment)
    
    async def _send_reply(self, comment: Comment, reply: str) -> bool:
        try:
            if comment.platform == SocialPlatform.FACEBOOK:
                return await self.social_client.facebook.reply_to_comment(
                    comment.id, reply
                )
            elif comment.platform == SocialPlatform.INSTAGRAM:
                return await self.social_client.instagram.reply_to_comment(
                    comment.id, reply
                )
            return False
        except Exception as e:
            logger.error(f"Failed to send reply: {e}")
            return False
    
    def get_pending_comments(self) -> List[Comment]:
        return [c for c in self._comment_queue if not c.replied and c.needs_reply]
    
    def get_metrics(self, platform: Optional[SocialPlatform] = None) -> CommunityMetrics:
        relevant_comments = self._comment_queue
        
        if platform:
            relevant_comments = [c for c in relevant_comments if c.platform == platform]
        
        total_comments = len(relevant_comments)
        total_replies = len([c for c in relevant_comments if c.replied])
        
        sentiment_counts = {
            CommentSentiment.POSITIVE: 0,
            CommentSentiment.NEGATIVE: 0,
            CommentSentiment.NEUTRAL: 0,
        }
        
        for comment in relevant_comments:
            if comment.sentiment in sentiment_counts:
                sentiment_counts[comment.sentiment] += 1
        
        return CommunityMetrics(
            platform=platform or SocialPlatform.FACEBOOK,
            period="all_time",
            total_comments=total_comments,
            total_replies=total_replies,
            positive_sentiment=sentiment_counts[CommentSentiment.POSITIVE],
            negative_sentiment=sentiment_counts[CommentSentiment.NEGATIVE],
            neutral_sentiment=sentiment_counts[CommentSentiment.NEUTRAL],
            questions_answered=len([c for c in relevant_comments if c.sentiment == CommentSentiment.QUESTION and c.replied]),
            complaints_resolved=len([c for c in relevant_comments if c.sentiment == CommentSentiment.COMPLAINT and c.replied]),
            spam_detected=len([c for c in relevant_comments if c.sentiment == CommentSentiment.SPAM]),
        )


class CommunityAutomation:
    def __init__(self):
        self.monitor = CommunityMonitor()
        self._running = False
    
    async def start(self, check_interval: int = 300) -> None:
        self._running = True
        
        while self._running:
            try:
                new_comments = await self.monitor.check_comments()
                
                for comment in new_comments:
                    if comment.needs_reply:
                        reply = await self.monitor.process_comment(comment)
                        if reply:
                            logger.info(f"Generated reply for comment {comment.id}: {reply[:50]}...")
                
                await asyncio.sleep(check_interval)
                
            except Exception as e:
                logger.error(f"Error in community automation: {e}")
                await asyncio.sleep(60)
    
    def stop(self) -> None:
        self._running = False
    
    async def add_post_to_monitor(
        self,
        platform: SocialPlatform,
        post_id: str
    ) -> None:
        await self.monitor.start_monitoring(platform, post_id)
    
    async def remove_post_from_monitor(
        self,
        platform: SocialPlatform,
        post_id: str
    ) -> None:
        await self.monitor.stop_monitoring(platform, post_id)
    
    def get_pending_replies(self) -> List[Comment]:
        return self.monitor.get_pending_comments()
    
    async def approve_reply(self, comment_id: str, custom_reply: Optional[str] = None) -> bool:
        for comment in self.monitor._comment_queue:
            if comment.id == comment_id:
                reply = custom_reply or comment.reply_content
                if reply:
                    success = await self.monitor._send_reply(comment, reply)
                    if success:
                        comment.replied = True
                        comment.reply_content = reply
                        return True
        return False
    
    async def reject_reply(self, comment_id: str) -> bool:
        for comment in self.monitor._comment_queue:
            if comment.id == comment_id:
                comment.needs_reply = False
                return True
        return False
