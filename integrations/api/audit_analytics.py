"""
AI 审核工作流 API - 历史追溯和驳回分析
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
import json

from agentforge.database.db import get_db
from agentforge.security.jwt_handler import get_current_user

router = APIRouter(prefix="/api/audit", tags=["AI Audit"])


@router.get("/history")
async def get_audit_history(
    days: int = Query(default=30, ge=1, le=365),
    status: Optional[str] = None,
    item_type: Optional[str] = None,
    limit: int = Query(default=100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取审核历史记录
    
    Args:
        days: 查询最近 N 天的记录
        status: 按状态过滤
        item_type: 按类型过滤
        limit: 返回数量限制
    """
    from agentforge.models import AuditLog
    
    # 计算日期范围
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # 构建查询条件
    conditions = [
        AuditLog.created_at >= start_date,
        AuditLog.created_at <= end_date
    ]
    
    if status:
        conditions.append(AuditLog.status == status)
    
    if item_type:
        conditions.append(AuditLog.item_type == item_type)
    
    # 执行查询
    query = select(AuditLog).where(and_(*conditions)).order_by(AuditLog.created_at.desc()).limit(limit)
    result = await db.execute(query)
    logs = result.scalars().all()
    
    # 格式化返回
    history = []
    for log in logs:
        history.append({
            "id": log.id,
            "item_id": log.item_id,
            "item_type": log.item_type,
            "action": log.action,  # approved, rejected, modified
            "original_content": log.original_content,
            "final_content": log.final_content,
            "reject_reason": log.reject_reason,
            "modified_by": log.modified_by,
            "reviewed_by": log.reviewed_by,
            "review_duration": log.review_duration,  # 秒
            "created_at": log.created_at.isoformat(),
            "metadata": log.metadata
        })
    
    return {
        "items": history,
        "total": len(history),
        "period": f"{days} days"
    }


@router.get("/history/{item_id}/versions")
async def get_item_versions(
    item_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取单个审核项的所有版本历史"""
    from agentforge.models import AuditLog
    
    query = select(AuditLog).where(AuditLog.item_id == item_id).order_by(AuditLog.created_at.asc())
    result = await db.execute(query)
    logs = result.scalars().all()
    
    if not logs:
        raise HTTPException(status_code=404, detail="Item not found")
    
    versions = []
    for log in logs:
        versions.append({
            "version": len(versions) + 1,
            "action": log.action,
            "content": log.final_content,
            "modified_by": log.modified_by,
            "reviewed_by": log.reviewed_by,
            "timestamp": log.created_at.isoformat(),
            "notes": log.reject_reason or log.metadata.get("notes", "")
        })
    
    return {
        "item_id": item_id,
        "versions": versions,
        "total_versions": len(versions)
    }


@router.get("/trend")
async def get_audit_trend(
    days: int = Query(default=7, ge=1, le=30),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取审核趋势数据"""
    from agentforge.models import AuditLog
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # 按日期分组统计
    trend_data = []
    
    for i in range(days):
        date = start_date + timedelta(days=i)
        date_str = date.strftime("%m-%d")
        
        # 查询当天的统计
        day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = date.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        conditions = [
            AuditLog.created_at >= day_start,
            AuditLog.created_at <= day_end
        ]
        
        # 统计各状态数量
        approved_query = select(func.count()).select_from(AuditLog).where(
            and_(*conditions, AuditLog.status == "approved")
        )
        rejected_query = select(func.count()).select_from(AuditLog).where(
            and_(*conditions, AuditLog.status == "rejected")
        )
        pending_query = select(func.count()).select_from(AuditLog).where(
            and_(*conditions, AuditLog.status == "pending")
        )
        
        approved = await db.execute(approved_query)
        rejected = await db.execute(rejected_query)
        pending = await db.execute(pending_query)
        
        trend_data.append({
            "date": date_str,
            "approved": approved.scalar() or 0,
            "rejected": rejected.scalar() or 0,
            "pending": pending.scalar() or 0
        })
    
    return {"trend": trend_data, "period": f"{days} days"}


@router.get("/analytics/rejection")
async def get_rejection_analytics(
    days: int = Query(default=30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取驳回分析数据"""
    from agentforge.models import AuditLog
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # 查询所有驳回记录
    query = select(AuditLog).where(
        and_(
            AuditLog.created_at >= start_date,
            AuditLog.created_at <= end_date,
            AuditLog.action == "rejected"
        )
    )
    result = await db.execute(query)
    rejected_logs = result.scalars().all()
    
    # 统计驳回原因
    reason_stats = {}
    type_stats = {}
    hourly_stats = {hour: 0 for hour in range(24)}
    
    for log in rejected_logs:
        # 统计原因
        reason = log.reject_reason or "未指定原因"
        reason_stats[reason] = reason_stats.get(reason, 0) + 1
        
        # 统计类型
        item_type = log.item_type or "unknown"
        type_stats[item_type] = type_stats.get(item_type, 0) + 1
        
        # 统计小时分布
        hour = log.created_at.hour
        hourly_stats[hour] = hourly_stats.get(hour, 0) + 1
    
    # 计算趋势
    total_rejected = len(rejected_logs)
    total_items = len(rejected_logs)  # TODO: 需要查询总数
    
    # 生成改进建议
    suggestions = []
    if reason_stats:
        top_reason = max(reason_stats.items(), key=lambda x: x[1])
        suggestions.append(f"主要驳回原因：{top_reason[0]} ({top_reason[1]}次)")
    
    if type_stats:
        top_type = max(type_stats.items(), key=lambda x: x[1])
        suggestions.append(f"驳回最多的类型：{top_type[0]} ({top_type[1]}次)")
    
    return {
        "summary": {
            "total_rejected": total_rejected,
            "rejection_rate": total_rejected / max(total_items, 1),
            "period": f"{days} days"
        },
        "reasons": reason_stats,
        "by_type": type_stats,
        "hourly_distribution": hourly_stats,
        "suggestions": suggestions
    }


@router.get("/analytics/performance")
async def get_performance_analytics(
    days: int = Query(default=7, ge=1, le=30),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取审核性能分析"""
    from agentforge.models import AuditLog
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # 查询审核时长
    query = select(AuditLog.review_duration).where(
        and_(
            AuditLog.created_at >= start_date,
            AuditLog.created_at <= end_date,
            AuditLog.review_duration.isnot(None)
        )
    )
    result = await db.execute(query)
    durations = result.scalars().all()
    
    if not durations:
        return {
            "avg_duration": 0,
            "p50_duration": 0,
            "p95_duration": 0,
            "p99_duration": 0
        }
    
    # 计算统计值
    sorted_durations = sorted(durations)
    total = len(sorted_durations)
    
    avg_duration = sum(sorted_durations) / total
    p50_index = int(total * 0.5)
    p95_index = int(total * 0.95)
    p99_index = int(total * 0.99)
    
    return {
        "avg_duration": avg_duration,
        "p50_duration": sorted_durations[p50_index],
        "p95_duration": sorted_durations[p95_index],
        "p99_duration": sorted_durations[p99_index] if p99_index < total else sorted_durations[-1],
        "total_reviews": total,
        "period": f"{days} days"
    }


@router.post("/batch/approve")
async def batch_approve(
    ids: List[str],
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """批量通过审核项"""
    from agentforge.models import AuditItem, AuditLog
    
    # 更新状态
    for item_id in ids:
        query = select(AuditItem).where(AuditItem.id == item_id)
        result = await db.execute(query)
        item = result.scalar_one_or_none()
        
        if item:
            item.status = "approved"
            item.reviewed_by = current_user.get("user_id")
            
            # 记录日志
            log = AuditLog(
                item_id=item_id,
                item_type=item.type,
                action="approved",
                original_content=item.content,
                final_content=item.content,
                reviewed_by=current_user.get("user_id"),
                metadata={"batch": True}
            )
            db.add(log)
    
    await db.commit()
    
    return {
        "success": True,
        "approved_count": len(ids),
        "message": f"已成功通过 {len(ids)} 个项目"
    }


@router.post("/batch/reject")
async def batch_reject(
    ids: List[str],
    reason: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """批量驳回审核项"""
    from agentforge.models import AuditItem, AuditLog
    
    # 更新状态
    for item_id in ids:
        query = select(AuditItem).where(AuditItem.id == item_id)
        result = await db.execute(query)
        item = result.scalar_one_or_none()
        
        if item:
            item.status = "rejected"
            item.reviewed_by = current_user.get("user_id")
            
            # 记录日志
            log = AuditLog(
                item_id=item_id,
                item_type=item.type,
                action="rejected",
                original_content=item.content,
                final_content=item.content,
                reject_reason=reason,
                reviewed_by=current_user.get("user_id"),
                metadata={"batch": True, "reason": reason}
            )
            db.add(log)
    
    await db.commit()
    
    return {
        "success": True,
        "rejected_count": len(ids),
        "message": f"已成功驳回 {len(ids)} 个项目"
    }
