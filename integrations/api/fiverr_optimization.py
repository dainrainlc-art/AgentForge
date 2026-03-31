"""
Fiverr 主页优化 API

提供优化建议的生成、查询和管理功能
"""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from loguru import logger

from agentforge.fiverr.optimization import (
    FiverrOptimizationEngine,
    FiverrProfileData,
    OptimizationCategory,
    Priority
)

router = APIRouter(prefix="/api/fiverr/optimization", tags=["Fiverr 优化"])

# 引擎实例（实际应用中应该使用单例或依赖注入）
_engines: Dict[str, FiverrOptimizationEngine] = {}


def get_engine(username: str) -> FiverrOptimizationEngine:
    """获取或创建优化引擎"""
    if username not in _engines:
        _engines[username] = FiverrOptimizationEngine()
    return _engines[username]


class ProfileDataRequest(BaseModel):
    """主页数据请求"""
    username: str
    level: str = "New Seller"
    rating: float = 0.0
    total_reviews: int = 0
    total_orders: int = 0
    completion_rate: float = 0.0
    on_time_delivery: float = 0.0
    response_time: float = 0.0
    gigs_count: int = 0
    total_earnings: float = 0.0
    profile_views: int = 0
    gig_impressions: int = 0
    gig_clicks: int = 0
    orders_in_queue: int = 0


class SuggestionUpdateRequest(BaseModel):
    """建议更新请求"""
    status: str


@router.post("/analyze")
async def analyze_profile(request: ProfileDataRequest):
    """
    分析 Fiverr 主页并生成优化建议
    
    接收卖家的主页数据，使用 AI 分析并生成个性化的优化建议。
    """
    try:
        logger.info(f"分析主页：{request.username}")
        
        engine = get_engine(request.username)
        
        # 转换为 Pydantic 模型
        profile_data = FiverrProfileData(**request.model_dump())
        
        # 生成建议
        suggestions = await engine.analyze_profile(profile_data)
        
        return {
            "success": True,
            "username": request.username,
            "suggestions_count": len(suggestions),
            "suggestions": [s.model_dump() for s in suggestions]
        }
    
    except Exception as e:
        logger.error(f"分析失败：{e}")
        raise HTTPException(status_code=500, detail=f"分析失败：{str(e)}")


@router.get("/suggestions/{username}")
async def get_suggestions(
    username: str,
    category: Optional[str] = None,
    priority: Optional[str] = None,
    status: Optional[str] = None
):
    """
    获取优化建议
    
    支持按类别、优先级和状态过滤
    """
    try:
        engine = get_engine(username)
        
        # 转换枚举值
        category_enum = OptimizationCategory(category) if category else None
        priority_enum = Priority(priority) if priority else None
        
        suggestions = engine.get_suggestions(
            category=category_enum,
            priority=priority_enum,
            status=status
        )
        
        return {
            "success": True,
            "count": len(suggestions),
            "suggestions": [s.model_dump() for s in suggestions]
        }
    
    except Exception as e:
        logger.error(f"获取建议失败：{e}")
        raise HTTPException(status_code=500, detail=f"获取建议失败：{str(e)}")


@router.patch("/suggestions/{username}/{suggestion_id}")
async def update_suggestion(
    username: str,
    suggestion_id: str,
    request: SuggestionUpdateRequest
):
    """
    更新优化建议状态
    
    可更新的状态：pending, in_progress, completed, rejected
    """
    try:
        engine = get_engine(username)
        
        success = engine.update_suggestion_status(suggestion_id, request.status)
        
        if not success:
            raise HTTPException(status_code=404, detail="建议不存在")
        
        return {
            "success": True,
            "suggestion_id": suggestion_id,
            "new_status": request.status
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新建议失败：{e}")
        raise HTTPException(status_code=500, detail=f"更新建议失败：{str(e)}")


@router.get("/progress/{username}")
async def get_progress_report(username: str):
    """
    获取优化进度报告
    
    返回各类别、优先级和状态的统计信息
    """
    try:
        engine = get_engine(username)
        report = engine.get_progress_report()
        
        return {
            "success": True,
            "username": username,
            "report": report
        }
    
    except Exception as e:
        logger.error(f"获取进度报告失败：{e}")
        raise HTTPException(status_code=500, detail=f"获取进度报告失败：{str(e)}")


@router.post("/reset/{username}")
async def reset_suggestions(username: str):
    """
    重置优化建议
    
    清除所有已生成的建议，可以重新分析
    """
    try:
        if username in _engines:
            del _engines[username]
        
        return {
            "success": True,
            "message": f"已重置 {username} 的优化建议"
        }
    
    except Exception as e:
        logger.error(f"重置失败：{e}")
        raise HTTPException(status_code=500, detail=f"重置失败：{str(e)}")
