"""
社交媒体分析增强 API

提供多维度数据分析、趋势预测和可视化数据生成功能
"""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from loguru import logger

from agentforge.social.analytics_enhanced import (
    AdvancedAnalyticsEngine,
    PostMetrics,
    AnalyticsPeriod,
    Platform,
    AnalyticsReport
)

router = APIRouter(prefix="/api/social/analytics", tags=["社交媒体分析"])

# 引擎实例（实际应用中应该使用单例或依赖注入）
_engines: Dict[str, AdvancedAnalyticsEngine] = {}


def get_engine(user_id: str) -> AdvancedAnalyticsEngine:
    """获取或创建分析引擎"""
    if user_id not in _engines:
        _engines[user_id] = AdvancedAnalyticsEngine()
    return _engines[user_id]


class MetricsInput(BaseModel):
    """指标输入"""
    post_id: str
    platform: str
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


@router.post("/metrics")
async def add_metrics(user_id: str, metrics: MetricsInput):
    """
    添加帖子指标数据
    
    收集并存储帖子的表现数据，用于后续分析
    """
    try:
        engine = get_engine(user_id)
        
        # 转换为 PostMetrics
        post_metrics = PostMetrics(
            post_id=metrics.post_id,
            platform=Platform(metrics.platform),
            impressions=metrics.impressions,
            reach=metrics.reach,
            engagement=metrics.engagement,
            likes=metrics.likes,
            comments=metrics.comments,
            shares=metrics.shares,
            clicks=metrics.clicks,
            saves=metrics.saves,
            video_views=metrics.video_views,
            profile_visits=metrics.profile_visits,
            engagement_rate=metrics.engagement_rate,
            click_through_rate=metrics.click_through_rate
        )
        
        engine.add_metrics(post_metrics)
        
        return {
            "success": True,
            "message": f"已添加帖子 {metrics.post_id} 的指标数据",
            "post_id": metrics.post_id
        }
    
    except Exception as e:
        logger.error(f"添加指标失败：{e}")
        raise HTTPException(status_code=500, detail=f"添加指标失败：{str(e)}")


@router.get("/report/{user_id}")
async def generate_report(
    user_id: str,
    period: str = Query(default="7d", description="分析周期：24h, 7d, 30d, 90d"),
    platforms: Optional[str] = Query(default=None, description="平台列表，逗号分隔")
):
    """
    生成分析报告
    
    生成多维度的社交媒体表现分析报告，包括趋势、对比和洞察
    """
    try:
        engine = get_engine(user_id)
        
        # 转换周期
        period_enum = AnalyticsPeriod(period)
        
        # 转换平台列表
        platform_list = None
        if platforms:
            platform_list = [Platform(p.strip()) for p in platforms.split(",")]
        
        # 生成报告
        report = engine.generate_report(period_enum, platform_list)
        
        return {
            "success": True,
            "user_id": user_id,
            "period": period,
            "report": report.model_dump()
        }
    
    except Exception as e:
        logger.error(f"生成报告失败：{e}")
        raise HTTPException(status_code=500, detail=f"生成报告失败：{str(e)}")


@router.get("/insights/{user_id}")
async def get_insights(
    user_id: str,
    period: str = Query(default="7d", description="分析周期：24h, 7d, 30d, 90d")
):
    """
    获取分析洞察
    
    获取 AI 生成的智能分析洞察和建议
    """
    try:
        engine = get_engine(user_id)
        period_enum = AnalyticsPeriod(period)
        
        report = engine.generate_report(period_enum)
        
        return {
            "success": True,
            "user_id": user_id,
            "period": period,
            "insights_count": len(report.insights),
            "insights": [i.model_dump() for i in report.insights]
        }
    
    except Exception as e:
        logger.error(f"获取洞察失败：{e}")
        raise HTTPException(status_code=500, detail=f"获取洞察失败：{str(e)}")


@router.get("/trends/{user_id}")
async def get_trends(
    user_id: str,
    metric_type: str = Query(default="impressions", description="指标类型：impressions, engagement, followers")
):
    """
    获取趋势数据
    
    获取特定指标的时间序列趋势数据
    """
    try:
        engine = get_engine(user_id)
        report = engine.generate_report(AnalyticsPeriod.LAST_7_DAYS)
        
        trends_map = {
            "impressions": report.impression_trend,
            "engagement": report.engagement_trend,
            "followers": report.follower_trend
        }
        
        trends = trends_map.get(metric_type, report.impression_trend)
        
        return {
            "success": True,
            "user_id": user_id,
            "metric_type": metric_type,
            "trends": [t.model_dump() for t in trends]
        }
    
    except Exception as e:
        logger.error(f"获取趋势失败：{e}")
        raise HTTPException(status_code=500, detail=f"获取趋势失败：{str(e)}")


@router.get("/comparison/{user_id}")
async def get_comparison(user_id: str):
    """
    获取对比数据
    
    获取各平台和内容类型的对比数据
    """
    try:
        engine = get_engine(user_id)
        report = engine.generate_report(AnalyticsPeriod.LAST_7_DAYS)
        
        return {
            "success": True,
            "user_id": user_id,
            "platform_comparison": [c.model_dump() for c in report.platform_comparison],
            "content_type_performance": [c.model_dump() for c in report.content_type_performance]
        }
    
    except Exception as e:
        logger.error(f"获取对比数据失败：{e}")
        raise HTTPException(status_code=500, detail=f"获取对比数据失败：{str(e)}")


@router.get("/charts/{user_id}")
async def get_chart_configs(user_id: str):
    """
    获取图表配置
    
    获取前端可视化所需的图表配置数据
    """
    try:
        engine = get_engine(user_id)
        report = engine.generate_report(AnalyticsPeriod.LAST_7_DAYS)
        
        return {
            "success": True,
            "user_id": user_id,
            "charts": report.charts
        }
    
    except Exception as e:
        logger.error(f"获取图表配置失败：{e}")
        raise HTTPException(status_code=500, detail=f"获取图表配置失败：{str(e)}")


@router.post("/export/{user_id}")
async def export_report(
    user_id: str,
    period: str = Query(default="7d", description="分析周期"),
    format: str = Query(default="json", description="导出格式：json")
):
    """
    导出分析报告
    
    导出完整分析报告为指定格式
    """
    try:
        engine = get_engine(user_id)
        period_enum = AnalyticsPeriod(period)
        
        report = engine.generate_report(period_enum)
        exported = engine.export_report(report, format)
        
        return {
            "success": True,
            "user_id": user_id,
            "period": period,
            "format": format,
            "report": exported
        }
    
    except Exception as e:
        logger.error(f"导出报告失败：{e}")
        raise HTTPException(status_code=500, detail=f"导出报告失败：{str(e)}")


@router.delete("/reset/{user_id}")
async def reset_data(user_id: str):
    """
    重置分析数据
    
    清除所有已收集的数据，重新开始
    """
    try:
        if user_id in _engines:
            del _engines[user_id]
        
        return {
            "success": True,
            "message": f"已重置用户 {user_id} 的分析数据"
        }
    
    except Exception as e:
        logger.error(f"重置数据失败：{e}")
        raise HTTPException(status_code=500, detail=f"重置数据失败：{str(e)}")
