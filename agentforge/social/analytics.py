"""
Social Media Analytics - Post performance analysis
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from loguru import logger
from enum import Enum

from agentforge.social.content_adapter import Platform


class MetricType(str, Enum):
    IMPRESSIONS = "impressions"
    REACH = "reach"
    ENGAGEMENT = "engagement"
    LIKES = "likes"
    COMMENTS = "comments"
    SHARES = "shares"
    CLICKS = "clicks"
    SAVES = "saves"
    VIDEO_VIEWS = "video_views"
    PROFILE_VISITS = "profile_visits"


class PostMetrics(BaseModel):
    """Post performance metrics"""
    post_id: str
    platform: Platform
    collected_at: datetime = Field(default_factory=datetime.now)
    impressions: int = 0
    reach: int = 0
    engagement: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    clicks: int = 0
    saves: int = 0
    video_views: int = 0
    profile_visits: int = 0
    engagement_rate: float = 0.0
    click_through_rate: float = 0.0


class AnalyticsPeriod(str, Enum):
    LAST_24_HOURS = "24h"
    LAST_7_DAYS = "7d"
    LAST_30_DAYS = "30d"
    LAST_90_DAYS = "90d"


class PlatformAnalytics(BaseModel):
    """Analytics summary for a platform"""
    platform: Platform
    period: AnalyticsPeriod
    total_posts: int = 0
    total_impressions: int = 0
    total_reach: int = 0
    total_engagement: int = 0
    average_engagement_rate: float = 0.0
    best_posting_times: List[int] = Field(default_factory=list)
    top_posts: List[str] = Field(default_factory=list)
    growth_rate: float = 0.0


class ContentPerformance(BaseModel):
    """Content performance analysis"""
    content_type: str
    average_engagement_rate: float
    best_performing_platform: Platform
    recommendations: List[str] = Field(default_factory=list)


class SocialAnalytics:
    """Social media analytics engine"""
    
    BENCHMARK_RATES = {
        Platform.TWITTER: {"engagement": 0.5, "ctr": 1.5},
        Platform.LINKEDIN: {"engagement": 2.0, "ctr": 0.5},
        Platform.INSTAGRAM: {"engagement": 3.0, "ctr": 0.1},
        Platform.FACEBOOK: {"engagement": 0.5, "ctr": 0.9},
        Platform.YOUTUBE: {"engagement": 4.0, "ctr": 2.0},
        Platform.TIKTOK: {"engagement": 8.0, "ctr": 1.0},
    }
    
    def __init__(self):
        self._metrics_history: Dict[str, List[PostMetrics]] = {}
        self._analytics_cache: Dict[str, PlatformAnalytics] = {}
    
    def record_metrics(self, metrics: PostMetrics) -> None:
        """Record post metrics"""
        
        if metrics.post_id not in self._metrics_history:
            self._metrics_history[metrics.post_id] = []
        
        self._metrics_history[metrics.post_id].append(metrics)
        
        metrics.engagement_rate = self._calculate_engagement_rate(metrics)
        metrics.click_through_rate = self._calculate_ctr(metrics)
        
        logger.info(f"Recorded metrics for post {metrics.post_id}")
    
    def _calculate_engagement_rate(self, metrics: PostMetrics) -> float:
        """Calculate engagement rate"""
        
        if metrics.impressions == 0:
            return 0.0
        
        total_engagement = (
            metrics.likes + metrics.comments + metrics.shares +
            metrics.saves + metrics.clicks
        )
        
        return round((total_engagement / metrics.impressions) * 100, 2)
    
    def _calculate_ctr(self, metrics: PostMetrics) -> float:
        """Calculate click-through rate"""
        
        if metrics.impressions == 0:
            return 0.0
        
        return round((metrics.clicks / metrics.impressions) * 100, 2)
    
    def get_post_metrics(
        self,
        post_id: str,
        latest: bool = True
    ) -> Optional[PostMetrics]:
        """Get metrics for a specific post"""
        
        history = self._metrics_history.get(post_id)
        
        if not history:
            return None
        
        if latest:
            return history[-1]
        
        return history[0]
    
    def get_metrics_history(
        self,
        post_id: str
    ) -> List[PostMetrics]:
        """Get full metrics history for a post"""
        
        return self._metrics_history.get(post_id, [])
    
    def analyze_platform(
        self,
        platform: Platform,
        period: AnalyticsPeriod = AnalyticsPeriod.LAST_7_DAYS
    ) -> PlatformAnalytics:
        """Analyze platform performance"""
        
        now = datetime.now()
        
        period_deltas = {
            AnalyticsPeriod.LAST_24_HOURS: timedelta(hours=24),
            AnalyticsPeriod.LAST_7_DAYS: timedelta(days=7),
            AnalyticsPeriod.LAST_30_DAYS: timedelta(days=30),
            AnalyticsPeriod.LAST_90_DAYS: timedelta(days=90),
        }
        
        cutoff = now - period_deltas[period]
        
        relevant_metrics = [
            m for history in self._metrics_history.values()
            for m in history
            if m.platform == platform and m.collected_at >= cutoff
        ]
        
        if not relevant_metrics:
            return PlatformAnalytics(
                platform=platform,
                period=period
            )
        
        total_impressions = sum(m.impressions for m in relevant_metrics)
        total_reach = sum(m.reach for m in relevant_metrics)
        total_engagement = sum(
            m.likes + m.comments + m.shares for m in relevant_metrics
        )
        
        avg_engagement_rate = sum(m.engagement_rate for m in relevant_metrics) / len(relevant_metrics)
        
        posting_hours = {}
        for m in relevant_metrics:
            hour = m.collected_at.hour
            posting_hours[hour] = posting_hours.get(hour, 0) + m.engagement_rate
        
        best_times = sorted(
            posting_hours.keys(),
            key=lambda h: posting_hours[h],
            reverse=True
        )[:3]
        
        top_posts = sorted(
            relevant_metrics,
            key=lambda m: m.engagement_rate,
            reverse=True
        )[:5]
        
        return PlatformAnalytics(
            platform=platform,
            period=period,
            total_posts=len(set(m.post_id for m in relevant_metrics)),
            total_impressions=total_impressions,
            total_reach=total_reach,
            total_engagement=total_engagement,
            average_engagement_rate=round(avg_engagement_rate, 2),
            best_posting_times=best_times,
            top_posts=[p.post_id for p in top_posts]
        )
    
    def compare_performance(
        self,
        metrics: PostMetrics
    ) -> Dict[str, Any]:
        """Compare post performance against benchmarks"""
        
        benchmark = self.BENCHMARK_RATES.get(metrics.platform, {})
        benchmark_engagement = benchmark.get("engagement", 1.0)
        benchmark_ctr = benchmark.get("ctr", 1.0)
        
        engagement_comparison = "above" if metrics.engagement_rate > benchmark_engagement else "below"
        ctr_comparison = "above" if metrics.click_through_rate > benchmark_ctr else "below"
        
        return {
            "platform": metrics.platform.value,
            "engagement_rate": metrics.engagement_rate,
            "benchmark_engagement": benchmark_engagement,
            "engagement_status": engagement_comparison,
            "ctr": metrics.click_through_rate,
            "benchmark_ctr": benchmark_ctr,
            "ctr_status": ctr_comparison,
            "overall_score": self._calculate_score(metrics, benchmark)
        }
    
    def _calculate_score(
        self,
        metrics: PostMetrics,
        benchmark: Dict[str, float]
    ) -> int:
        """Calculate overall performance score (0-100)"""
        
        score = 50
        
        if metrics.engagement_rate > benchmark.get("engagement", 1.0):
            score += 25
        else:
            score -= 10
        
        if metrics.click_through_rate > benchmark.get("ctr", 1.0):
            score += 15
        else:
            score -= 5
        
        if metrics.comments > metrics.likes * 0.1:
            score += 10
        
        return max(0, min(100, score))
    
    def get_recommendations(
        self,
        platform: Platform,
        metrics: Optional[PostMetrics] = None
    ) -> List[str]:
        """Get performance improvement recommendations"""
        
        recommendations = []
        
        if metrics:
            comparison = self.compare_performance(metrics)
            
            if comparison["engagement_status"] == "below":
                recommendations.append(
                    f"Engagement rate is below benchmark ({metrics.engagement_rate}% vs {comparison['benchmark_engagement']}%). "
                    "Consider using more engaging content formats or posting at optimal times."
                )
            
            if comparison["ctr_status"] == "below":
                recommendations.append(
                    f"CTR is below benchmark. Consider adding clear call-to-actions or optimizing link previews."
                )
            
            if metrics.comments < metrics.likes * 0.05:
                recommendations.append(
                    "Low comment ratio. Try asking questions or creating discussion-worthy content."
                )
        
        platform_tips = {
            Platform.TWITTER: [
                "Use threads for longer content",
                "Include relevant hashtags (2-3 max)",
                "Post during peak hours (9AM, 12PM, 5-6PM)"
            ],
            Platform.LINKEDIN: [
                "Write longer, professional content",
                "Use industry-specific hashtags",
                "Engage with comments within first hour"
            ],
            Platform.INSTAGRAM: [
                "Use carousel posts for higher engagement",
                "Include location tags",
                "Post during lunch and evening hours"
            ],
            Platform.FACEBOOK: [
                "Use native video content",
                "Encourage sharing with contests",
                "Post on weekdays between 1-4PM"
            ],
            Platform.YOUTUBE: [
                "Optimize video titles and thumbnails",
                "Use end screens and cards",
                "Encourage subscriptions in videos"
            ],
            Platform.TIKTOK: [
                "Use trending sounds",
                "Keep videos under 60 seconds",
                "Post multiple times per day"
            ],
        }
        
        recommendations.extend(platform_tips.get(platform, []))
        
        return recommendations
    
    def get_analytics_summary(
        self,
        platforms: Optional[List[Platform]] = None
    ) -> Dict[str, Any]:
        """Get overall analytics summary"""
        
        platforms = platforms or list(Platform)
        
        summary = {
            "platforms": {},
            "total_posts": 0,
            "total_impressions": 0,
            "total_engagement": 0,
            "best_platform": None,
            "generated_at": datetime.now().isoformat()
        }
        
        best_rate = 0
        
        for platform in platforms:
            analytics = self.analyze_platform(platform)
            
            summary["platforms"][platform.value] = analytics.model_dump()
            summary["total_posts"] += analytics.total_posts
            summary["total_impressions"] += analytics.total_impressions
            summary["total_engagement"] += analytics.total_engagement
            
            if analytics.average_engagement_rate > best_rate:
                best_rate = analytics.average_engagement_rate
                summary["best_platform"] = platform.value
        
        return summary


social_analytics = SocialAnalytics()
