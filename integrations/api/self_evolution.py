"""
自进化系统 API

提供自进化任务的触发、状态查询和配置管理
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from loguru import logger

from agentforge.core.self_evolution_scheduler import (
    get_evolution_manager,
    start_self_evolution,
    stop_self_evolution,
    run_self_evolution_now
)

router = APIRouter(prefix="/api/self-evolution", tags=["自进化系统"])


class EvolutionTaskRequest(BaseModel):
    """自进化任务请求"""
    task_type: str = "all"  # consolidation, self_check, review, all


class EvolutionStatusResponse(BaseModel):
    """自进化状态响应"""
    initialized: bool
    running: bool
    next_consolidation: str
    next_self_check: str
    next_review: str


@router.post("/start")
async def start_evolution():
    """
    启动自进化系统
    
    启动定时调度器，自动执行记忆巩固、自我检查和任务复盘
    """
    try:
        logger.info("启动自进化系统...")
        await start_self_evolution()
        
        return {
            "success": True,
            "message": "自进化系统已启动",
            "schedule": {
                "memory_consolidation": "03:00",
                "self_check": "04:00",
                "task_review": "23:00"
            }
        }
    
    except Exception as e:
        logger.error(f"启动自进化系统失败：{e}")
        raise HTTPException(status_code=500, detail=f"启动失败：{str(e)}")


@router.post("/stop")
async def stop_evolution():
    """
    停止自进化系统
    
    停止所有定时任务
    """
    try:
        logger.info("停止自进化系统...")
        await stop_self_evolution()
        
        return {
            "success": True,
            "message": "自进化系统已停止"
        }
    
    except Exception as e:
        logger.error(f"停止自进化系统失败：{e}")
        raise HTTPException(status_code=500, detail=f"停止失败：{str(e)}")


@router.post("/run")
async def run_evolution_now(request: EvolutionTaskRequest):
    """
    立即运行自进化任务
    
    手动触发指定的自进化任务，无需等待定时时间
    """
    try:
        logger.info(f"手动运行自进化任务：{request.task_type}")
        await run_self_evolution_now(request.task_type)
        
        return {
            "success": True,
            "message": f"任务 {request.task_type} 执行完成",
            "task_type": request.task_type
        }
    
    except Exception as e:
        logger.error(f"运行自进化任务失败：{e}")
        raise HTTPException(status_code=500, detail=f"执行失败：{str(e)}")


@router.get("/status")
async def get_evolution_status():
    """
    获取自进化系统状态
    
    返回系统初始化状态、运行状态和下次执行时间
    """
    try:
        manager = get_evolution_manager()
        status = manager.get_status()
        
        return {
            "success": True,
            "status": status
        }
    
    except Exception as e:
        logger.error(f"获取状态失败：{e}")
        raise HTTPException(status_code=500, detail=f"获取状态失败：{str(e)}")


@router.get("/schedule")
async def get_schedule():
    """
    获取定时任务配置
    
    返回所有定时任务的配置信息
    """
    schedule = {
        "memory_consolidation": {
            "time": "03:00",
            "description": "记忆巩固 - 去重、提取洞察、更新 MEMORY.md",
            "enabled": True
        },
        "self_check": {
            "time": "04:00",
            "description": "自我检查 - 分析错误日志、诊断问题、生成报告",
            "enabled": True
        },
        "task_review": {
            "time": "23:00",
            "description": "任务复盘 - 总结 completed 任务、提取经验教训",
            "enabled": True
        }
    }
    
    return {
        "success": True,
        "schedule": schedule
    }
