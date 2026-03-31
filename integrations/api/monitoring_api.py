"""
AgentForge Monitoring API
性能监控 API 端点
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional
from datetime import datetime

from agentforge.monitoring import monitor, init_monitoring

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


@router.get("/dashboard")
async def get_dashboard() -> Dict[str, Any]:
    """Get monitoring dashboard data"""
    return monitor.get_dashboard_data()


@router.get("/system")
async def get_system_metrics() -> Dict[str, Any]:
    """Get current system metrics"""
    metrics = monitor.get_system_metrics()
    return {
        "cpu_percent": metrics.cpu_percent,
        "memory_percent": metrics.memory_percent,
        "memory_used_gb": metrics.memory_used_gb,
        "memory_total_gb": metrics.memory_total_gb,
        "disk_percent": metrics.disk_percent,
        "disk_used_gb": metrics.disk_used_gb,
        "disk_total_gb": metrics.disk_total_gb,
        "network_sent_mb": metrics.network_sent_mb,
        "network_recv_mb": metrics.network_recv_mb,
        "timestamp": metrics.timestamp.isoformat()
    }


@router.get("/metrics/{metric_name}")
async def get_metric(
    metric_name: str,
    window_seconds: int = 300
) -> Dict[str, Any]:
    """Get specific metric data"""
    return monitor.get_metric_summary(metric_name, window_seconds)


@router.get("/metrics")
async def list_metrics() -> Dict[str, Any]:
    """List all registered metrics"""
    return {
        name: {
            "type": metric.type.value,
            "unit": metric.unit,
            "points_count": len(metric.points),
            "retention_seconds": metric.retention_seconds
        }
        for name, metric in monitor.metrics.items()
    }


@router.get("/requests")
async def get_request_stats(
    endpoint: Optional[str] = None
) -> Dict[str, Any]:
    """Get request statistics"""
    return monitor.get_request_stats(endpoint)


@router.get("/alerts")
async def get_alerts() -> Dict[str, Any]:
    """Get active alerts"""
    return {
        "active_alerts": [
            {
                "id": alert.id,
                "rule": alert.rule_name,
                "metric": alert.metric_name,
                "level": alert.level.value,
                "value": alert.current_value,
                "threshold": alert.threshold,
                "message": alert.message,
                "triggered_at": alert.triggered_at.isoformat()
            }
            for alert in monitor.active_alerts.values()
        ],
        "total": len(monitor.active_alerts)
    }


@router.post("/alerts/check")
async def check_alerts() -> Dict[str, Any]:
    """Manually trigger alert check"""
    monitor.check_alerts()
    return {
        "active_alerts": len(monitor.active_alerts),
        "status": "checked"
    }


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint"""
    system = monitor.get_system_metrics()
    
    status = "healthy"
    if system.cpu_percent > 95 or system.memory_percent > 95:
        status = "critical"
    elif system.cpu_percent > 80 or system.memory_percent > 85:
        status = "warning"
    
    return {
        "status": status,
        "timestamp": datetime.now().isoformat(),
        "metrics": {
            "cpu": system.cpu_percent,
            "memory": system.memory_percent,
            "disk": system.disk_percent
        }
    }


@router.post("/metrics/{metric_name}")
async def record_metric(
    metric_name: str,
    value: float,
    labels: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """Record a custom metric value"""
    monitor.record(metric_name, value, labels)
    return {"status": "recorded", "metric": metric_name, "value": value}


@router.get("/performance/summary")
async def performance_summary() -> Dict[str, Any]:
    """Get performance summary"""
    system = monitor.get_system_metrics()
    request_stats = monitor.get_request_stats()
    
    # Calculate overall health score
    health_score = 100
    
    # CPU impact
    if system.cpu_percent > 90:
        health_score -= 30
    elif system.cpu_percent > 70:
        health_score -= 15
    
    # Memory impact
    if system.memory_percent > 95:
        health_score -= 40
    elif system.memory_percent > 85:
        health_score -= 20
    
    # Error rate impact
    endpoints = request_stats.get("endpoints", [])
    avg_error_rate = sum(e.get("error_rate", 0) for e in endpoints) / len(endpoints) if endpoints else 0
    if avg_error_rate > 0.1:
        health_score -= 20
    elif avg_error_rate > 0.05:
        health_score -= 10
    
    return {
        "health_score": max(0, health_score),
        "status": "healthy" if health_score > 80 else "warning" if health_score > 50 else "critical",
        "system": {
            "cpu": system.cpu_percent,
            "memory": system.memory_percent,
            "disk": system.disk_percent
        },
        "requests": {
            "total_endpoints": len(endpoints),
            "avg_error_rate": avg_error_rate
        },
        "alerts": len(monitor.active_alerts)
    }
