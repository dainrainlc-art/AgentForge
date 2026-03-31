"""
Health Check API Endpoints
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any
from datetime import datetime
import asyncio

from agentforge.config import settings
from agentforge.llm import QianfanClient
from agentforge.memory import MemoryStore


router = APIRouter()


class HealthStatus(BaseModel):
    status: str
    timestamp: str
    version: str
    services: Dict[str, Any]


@router.get("/health", response_model=HealthStatus)
async def health_check():
    """Check overall system health"""
    
    services = {}
    
    llm_client = QianfanClient()
    try:
        llm_healthy = await llm_client.health_check()
        services["llm"] = {
            "status": "healthy" if llm_healthy else "degraded",
            "provider": "baidu_qianfan"
        }
    except Exception as e:
        services["llm"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    memory_store = MemoryStore()
    try:
        await memory_store.initialize()
        services["memory"] = {
            "status": "healthy",
            "redis": memory_store._redis is not None,
            "qdrant": memory_store._qdrant is not None
        }
    except Exception as e:
        services["memory"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    overall_status = "healthy"
    for service in services.values():
        if service.get("status") == "unhealthy":
            overall_status = "degraded"
            break
    
    return HealthStatus(
        status=overall_status,
        timestamp=datetime.now().isoformat(),
        version=settings.app_version,
        services=services
    )


@router.get("/health/live")
async def liveness():
    """Kubernetes liveness probe"""
    return {"status": "alive"}


@router.get("/health/ready")
async def readiness():
    """Kubernetes readiness probe"""
    return {"status": "ready"}
