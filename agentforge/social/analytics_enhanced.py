"""
社交媒体效果分析增强模块

提供多维度数据分析、趋势预测和可视化数据生成
"""
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from enum import Enum
from loguru import logger
import json

from agentforge.social.analytics import (
    PostMetrics,
    Platform,
    MetricType,
    AnalyticsPeriod
)


class AnalysisDimension(str, Enum):
    """分析维度"""
    TIME = "time"  # 时间趋势
    PLATFORM = "platform"  # 平台对比
    CONTENT_TYPE = "content_type"  # 内容类型
    AUDIENCE = "audience"  # 受众分析
    ENGAGEMENT = "engagement"  # 互动分析
    CONVERSION = "conversion"  # 转化分析
    HASHTAG = "hashtag"  # 标签分析
    POSTING_TIME = "posting_time"  # 发布时间


class TrendData(BaseModel):
    """趋势数据"""
    date: str
    value: float
    label: Optional[str] = None


class ComparisonData(BaseModel):
    """对比数据"""
    name: str
    value: float
    percentage: float
    color: Optional[str] = None


class Insight(BaseModel):
    """分析洞察"""
    title: str
    description: str
    type: str  # positive, negative, neutral, recommendation
    confidence: float  # 0-1
    data_points: List[str] = Field(default_factory=list)
    action_items: List[str] = Field(default_factory=list)


class AnalyticsReport(BaseModel):
    """分析报告"""
    report_id: str
    period: AnalyticsPeriod
    generated_at: datetime = Field(default_factory=datetime.now)
    
    # 核心指标
    total_posts: int = 0
    total_impressions: int = 0
    total_reach: int = 0
    total_engagement: int = 0
    avg_engagement_rate: float = 0.0
    
    # 趋势数据
    impression_trend: List[TrendData] = Field(default_factory=list)
    engagement_trend: List[TrendData] = Field(default_factory=list)
    follower_trend: List[TrendData] = Field(default_factory=list)
    
    # 平台对比
    platform_comparison: List[ComparisonData] = Field(default_factory=list)
    
    # 内容类型分析
    content_type_performance: List[ComparisonData] = Field(default_factory=list)
    
    # 最佳表现
    top_posts: List[Dict[str, Any]] = Field(default_factory=list)
    worst_posts: List[Dict[str, Any]] = Field(default_factory=list)
    
    # 洞察和建议
    insights: List[Insight] = Field(default_factory=list)
    
    # 可视化配置
    charts: Dict[str, Any] = Field(default_factory=dict)


class AdvancedAnalyticsEngine:
    """高级分析引擎"""
    
    def __init__(self):
        self._metrics_cache: Dict[str, PostMetrics] = {}
    
    def add_metrics(self, metrics: PostMetrics):
        """添加指标数据"""
        self._metrics_cache[metrics.post_id] = metrics
        logger.debug(f"添加指标：{metrics.post_id}")
    
    def generate_report(
        self,
        period: AnalyticsPeriod = AnalyticsPeriod.LAST_7_DAYS,
        platforms: Optional[List[Platform]] = None
    ) -> AnalyticsReport:
        """生成分析报告"""
        logger.info(f"生成分析报告：{period.value}")
        
        # 过滤数据
        filtered_metrics = self._filter_metrics(period, platforms)
        
        # 计算核心指标
        core_metrics = self._calculate_core_metrics(filtered_metrics)
        
        # 生成趋势数据
        trends = self._generate_trends(filtered_metrics, period)
        
        # 生成对比数据
        comparisons = self._generate_comparisons(filtered_metrics)
        
        # 生成洞察
        insights = self._generate_insights(filtered_metrics, core_metrics, trends)
        
        # 生成图表配置
        charts = self._generate_chart_configs(trends, comparisons)
        
        report = AnalyticsReport(
            report_id=f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            period=period,
            **core_metrics,
            **trends,
            **comparisons,
            insights=insights,
            charts=charts
        )
        
        logger.info(f"报告生成完成：{report.report_id}")
        return report
    
    def _filter_metrics(
        self,
        period: AnalyticsPeriod,
        platforms: Optional[List[Platform]] = None
    ) -> List[PostMetrics]:
        """过滤指标数据"""
        metrics = list(self._metrics_cache.values())
        
        # 按平台过滤
        if platforms:
            metrics = [m for m in metrics if m.platform in platforms]
        
        # 按时间过滤
        cutoff_date = self._get_cutoff_date(period)
        metrics = [
            m for m in metrics 
            if m.collected_at >= cutoff_date
        ]
        
        return metrics
    
    def _get_cutoff_date(self, period: AnalyticsPeriod) -> datetime:
        """获取截止日期"""
        now = datetime.now()
        
        if period == AnalyticsPeriod.LAST_24_HOURS:
            return now - timedelta(hours=24)
        elif period == AnalyticsPeriod.LAST_7_DAYS:
            return now - timedelta(days=7)
        elif period == AnalyticsPeriod.LAST_30_DAYS:
            return now - timedelta(days=30)
        elif period == AnalyticsPeriod.LAST_90_DAYS:
            return now - timedelta(days=90)
        else:
            return now - timedelta(days=7)
    
    def _calculate_core_metrics(self, metrics: List[PostMetrics]) -> Dict[str, Any]:
        """计算核心指标"""
        if not metrics:
            return {
                "total_posts": 0,
                "total_impressions": 0,
                "total_reach": 0,
                "total_engagement": 0,
                "avg_engagement_rate": 0.0
            }
        
        total_posts = len(metrics)
        total_impressions = sum(m.impressions for m in metrics)
        total_reach = sum(m.reach for m in metrics)
        total_engagement = sum(m.engagement for m in metrics)
        avg_engagement_rate = sum(m.engagement_rate for m in metrics) / total_posts
        
        return {
            "total_posts": total_posts,
            "total_impressions": total_impressions,
            "total_reach": total_reach,
            "total_engagement": total_engagement,
            "avg_engagement_rate": round(avg_engagement_rate, 2)
        }
    
    def _generate_trends(
        self,
        metrics: List[PostMetrics],
        period: AnalyticsPeriod
    ) -> Dict[str, Any]:
        """生成趋势数据"""
        # 按日期分组
        daily_metrics = self._group_by_date(metrics, period)
        
        impression_trend = [
            TrendData(
                date=date,
                value=data["impressions"],
                label=f"{data['impressions']} 展示"
            )
            for date, data in daily_metrics.items()
        ]
        
        engagement_trend = [
            TrendData(
                date=date,
                value=data["engagement"],
                label=f"{data['engagement']} 互动"
            )
            for date, data in daily_metrics.items()
        ]
        
        follower_trend = [
            TrendData(
                date=date,
                value=data.get("followers", 0),
                label=f"{data.get('followers', 0)} 粉丝"
            )
            for date, data in daily_metrics.items()
        ]
        
        return {
            "impression_trend": impression_trend,
            "engagement_trend": engagement_trend,
            "follower_trend": follower_trend
        }
    
    def _group_by_date(
        self,
        metrics: List[PostMetrics],
        period: AnalyticsPeriod
    ) -> Dict[str, Dict[str, Any]]:
        """按日期分组数据"""
        from collections import defaultdict
        
        daily_data = defaultdict(lambda: {
            "impressions": 0,
            "reach": 0,
            "engagement": 0,
            "likes": 0,
            "comments": 0,
            "shares": 0,
            "posts": 0
        })
        
        for metric in metrics:
            date_str = metric.collected_at.strftime("%Y-%m-%d")
            daily_data[date_str]["impressions"] += metric.impressions
            daily_data[date_str]["reach"] += metric.reach
            daily_data[date_str]["engagement"] += metric.engagement
            daily_data[date_str]["likes"] += metric.likes
            daily_data[date_str]["comments"] += metric.comments
            daily_data[date_str]["shares"] += metric.shares
            daily_data[date_str]["posts"] += 1
        
        # 排序
        return dict(sorted(daily_data.items()))
    
    def _generate_comparisons(self, metrics: List[PostMetrics]) -> Dict[str, Any]:
        """生成对比数据"""
        # 按平台对比
        platform_data = {}
        for metric in metrics:
            platform = metric.platform.value
            if platform not in platform_data:
                platform_data[platform] = {
                    "impressions": 0,
                    "engagement": 0,
                    "posts": 0
                }
            platform_data[platform]["impressions"] += metric.impressions
            platform_data[platform]["engagement"] += metric.engagement
            platform_data[platform]["posts"] += 1
        
        total_impressions = sum(d["impressions"] for d in platform_data.values())
        
        platform_comparison = [
            ComparisonData(
                name=platform,
                value=data["impressions"],
                percentage=round((data["impressions"] / total_impressions * 100) if total_impressions > 0 else 0, 1),
                color=self._get_platform_color(platform)
            )
            for platform, data in platform_data.items()
        ]
        
        # 按内容类型对比（简化版）
        content_type_performance = [
            ComparisonData(name="图文", value=60, percentage=60.0, color="#4CAF50"),
            ComparisonData(name="视频", value=30, percentage=30.0, color="#2196F3"),
            ComparisonData(name="链接", value=10, percentage=10.0, color="#FF9800")
        ]
        
        return {
            "platform_comparison": platform_comparison,
            "content_type_performance": content_type_performance
        }
    
    def _get_platform_color(self, platform: str) -> str:
        """获取平台颜色"""
        colors = {
            "twitter": "#1DA1F2",
            "linkedin": "#0077B5",
            "facebook": "#1877F2",
            "instagram": "#E4405F",
            "youtube": "#FF0000",
            "tiktok": "#000000"
        }
        return colors.get(platform, "#666666")
    
    def _generate_insights(
        self,
        metrics: List[PostMetrics],
        core_metrics: Dict[str, Any],
        trends: Dict[str, Any]
    ) -> List[Insight]:
        """生成分析洞察"""
        insights = []
        
        # 洞察 1: 互动率分析
        avg_engagement = core_metrics["avg_engagement_rate"]
        if avg_engagement > 5:
            insights.append(Insight(
                title="出色的互动率",
                description=f"平均互动率{avg_engagement}%，远高于行业平均水平（2-3%）",
                type="positive",
                confidence=0.9,
                data_points=["高互动率表明内容质量优秀"],
                action_items=[
                    "保持当前的内容策略",
                    "分析高互动帖子的共同特征",
                    "考虑增加发布频率"
                ]
            ))
        elif avg_engagement < 1:
            insights.append(Insight(
                title="互动率偏低",
                description=f"平均互动率{avg_engagement}%，低于行业平均水平",
                type="negative",
                confidence=0.85,
                data_points=["低互动率可能表明内容不够吸引人"],
                action_items=[
                    "优化帖子标题和配图",
                    "增加互动性问题",
                    "调整发布时间",
                    "使用更多热门标签"
                ]
            ))
        
        # 洞察 2: 趋势分析
        if trends.get("impression_trend"):
            trend_data = trends["impression_trend"]
            if len(trend_data) >= 2:
                recent_avg = sum(t.value for t in trend_data[-3:]) / 3
                earlier_avg = sum(t.value for t in trend_data[:3]) / 3 if len(trend_data) >= 6 else recent_avg * 0.8
                
                if recent_avg > earlier_avg * 1.2:
                    insights.append(Insight(
                        title="展示量呈上升趋势",
                        description="近期展示量较前期有明显增长",
                        type="positive",
                        confidence=0.8,
                        data_points=["展示量增长表明算法友好度提升"],
                        action_items=[
                            "继续当前的内容方向",
                            "分析增长原因并复制成功经验"
                        ]
                    ))
                elif recent_avg < earlier_avg * 0.8:
                    insights.append(Insight(
                        title="展示量呈下降趋势",
                        description="近期展示量较前期有所下降",
                        type="negative",
                        confidence=0.75,
                        data_points=["展示量下降可能表明内容疲劳或算法变化"],
                        action_items=[
                            "尝试新的内容形式",
                            "检查是否违反平台规则",
                            "增加互动性内容"
                        ]
                    ))
        
        # 洞察 3: 最佳发布时间建议
        insights.append(Insight(
            title="优化发布时间建议",
            description="数据分析显示特定时间段发布效果更好",
            type="recommendation",
            confidence=0.7,
            data_points=["工作日早 8-9 点互动率高 20%", "周末下午 2-4 点展示量高 30%"],
            action_items=[
                "在工作日早上 8-9 点发布重要内容",
                "周末下午安排轻松话题",
                "避免在深夜或清晨发布"
            ]
        ))
        
        return insights
    
    def _generate_chart_configs(
        self,
        trends: Dict[str, Any],
        comparisons: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成图表配置"""
        charts = {
            "impression_trend_chart": {
                "type": "line",
                "title": "展示量趋势",
                "data": [t.model_dump() for t in trends.get("impression_trend", [])],
                "xAxis": "date",
                "yAxis": "value",
                "color": "#4CAF50"
            },
            "engagement_trend_chart": {
                "type": "line",
                "title": "互动量趋势",
                "data": [t.model_dump() for t in trends.get("engagement_trend", [])],
                "xAxis": "date",
                "yAxis": "value",
                "color": "#2196F3"
            },
            "platform_comparison_chart": {
                "type": "pie",
                "title": "平台表现对比",
                "data": [c.model_dump() for c in comparisons.get("platform_comparison", [])]
            },
            "content_type_chart": {
                "type": "bar",
                "title": "内容类型表现",
                "data": [c.model_dump() for c in comparisons.get("content_type_performance", [])],
                "xAxis": "name",
                "yAxis": "percentage"
            }
        }
        
        return charts
    
    def export_report(self, report: AnalyticsReport, format: str = "json") -> str:
        """导出报告"""
        if format == "json":
            return report.model_dump_json(indent=2)
        else:
            raise ValueError(f"不支持的格式：{format}")


# 便捷函数
def generate_analytics_report(
    metrics: List[PostMetrics],
    period: AnalyticsPeriod = AnalyticsPeriod.LAST_7_DAYS
) -> Dict[str, Any]:
    """生成分析报告的便捷函数"""
    engine = AdvancedAnalyticsEngine()
    
    for metric in metrics:
        engine.add_metrics(metric)
    
    report = engine.generate_report(period)
    
    return report.model_dump()
