"""
AgentForge Performance Monitoring Module
性能监控仪表盘
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum
from pydantic import BaseModel, Field
from collections import defaultdict
import asyncio
import psutil
import time
from loguru import logger


class MetricType(str, Enum):
    CPU = "cpu"
    MEMORY = "memory"
    DISK = "disk"
    NETWORK = "network"
    REQUEST = "request"
    LATENCY = "latency"
    ERROR = "error"
    CUSTOM = "custom"


class MetricPoint(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.now)
    value: float
    labels: Dict[str, str] = Field(default_factory=dict)


class MetricSeries(BaseModel):
    name: str
    type: MetricType
    unit: str
    points: List[MetricPoint] = Field(default_factory=list)
    retention_seconds: int = 3600  # 1 hour default


class AlertLevel(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertRule(BaseModel):
    name: str
    metric: str
    condition: str  # e.g., ">", "<", ">=", "<=", "=="
    threshold: float
    duration_seconds: int = 60
    level: AlertLevel = AlertLevel.WARNING
    enabled: bool = True


class Alert(BaseModel):
    id: str
    rule_name: str
    metric_name: str
    current_value: float
    threshold: float
    level: AlertLevel
    triggered_at: datetime = Field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None
    message: str = ""


class SystemMetrics(BaseModel):
    cpu_percent: float
    memory_percent: float
    memory_used_gb: float
    memory_total_gb: float
    disk_percent: float
    disk_used_gb: float
    disk_total_gb: float
    network_sent_mb: float
    network_recv_mb: float
    timestamp: datetime = Field(default_factory=datetime.now)


class PerformanceMonitor:
    def __init__(self, retention_seconds: int = 3600):
        self.metrics: Dict[str, MetricSeries] = {}
        self.alert_rules: List[AlertRule] = []
        self.active_alerts: Dict[str, Alert] = {}
        self.retention_seconds = retention_seconds
        
        self._request_counts: Dict[str, int] = defaultdict(int)
        self._request_latencies: Dict[str, List[float]] = defaultdict(list)
        self._error_counts: Dict[str, int] = defaultdict(int)
        
        self._monitoring = False
        self._monitor_task: Optional[asyncio.Task] = None
    
    def register_metric(
        self,
        name: str,
        metric_type: MetricType,
        unit: str = "",
        retention_seconds: Optional[int] = None
    ):
        """Register a new metric"""
        self.metrics[name] = MetricSeries(
            name=name,
            type=metric_type,
            unit=unit,
            retention_seconds=retention_seconds or self.retention_seconds
        )
        logger.info(f"Registered metric: {name}")
    
    def record(
        self,
        metric_name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None
    ):
        """Record a metric value"""
        if metric_name not in self.metrics:
            self.register_metric(metric_name, MetricType.CUSTOM)
        
        metric = self.metrics[metric_name]
        point = MetricPoint(value=value, labels=labels or {})
        metric.points.append(point)
        
        # Trim old points
        self._trim_metric(metric)
    
    def _trim_metric(self, metric: MetricSeries):
        """Remove old data points"""
        cutoff = datetime.now() - timedelta(seconds=metric.retention_seconds)
        metric.points = [p for p in metric.points if p.timestamp > cutoff]
    
    def add_alert_rule(self, rule: AlertRule):
        """Add an alert rule"""
        self.alert_rules.append(rule)
        logger.info(f"Added alert rule: {rule.name}")
    
    def check_alerts(self):
        """Check all alert rules"""
        for rule in self.alert_rules:
            if not rule.enabled:
                continue
            
            if rule.metric not in self.metrics:
                continue
            
            metric = self.metrics[rule.metric]
            if not metric.points:
                continue
            
            # Get latest value
            latest_value = metric.points[-1].value
            
            # Check condition
            triggered = False
            if rule.condition == ">" and latest_value > rule.threshold:
                triggered = True
            elif rule.condition == "<" and latest_value < rule.threshold:
                triggered = True
            elif rule.condition == ">=" and latest_value >= rule.threshold:
                triggered = True
            elif rule.condition == "<=" and latest_value <= rule.threshold:
                triggered = True
            elif rule.condition == "==" and latest_value == rule.threshold:
                triggered = True
            
            if triggered:
                if rule.name not in self.active_alerts:
                    alert = Alert(
                        id=f"alert_{len(self.active_alerts)}",
                        rule_name=rule.name,
                        metric_name=rule.metric,
                        current_value=latest_value,
                        threshold=rule.threshold,
                        level=rule.level,
                        message=f"{rule.name}: {latest_value} {metric.unit} {rule.condition} {rule.threshold}"
                    )
                    self.active_alerts[rule.name] = alert
                    logger.warning(f"Alert triggered: {alert.message}")
            else:
                if rule.name in self.active_alerts:
                    alert = self.active_alerts[rule.name]
                    alert.resolved_at = datetime.now()
                    del self.active_alerts[rule.name]
                    logger.info(f"Alert resolved: {rule.name}")
    
    def record_request(
        self,
        endpoint: str,
        method: str = "GET",
        status_code: int = 200,
        latency_ms: float = 0.0
    ):
        """Record HTTP request metrics"""
        key = f"{method}:{endpoint}"
        self._request_counts[key] += 1
        self._request_latencies[key].append(latency_ms)
        
        # Keep only last 1000 latencies
        if len(self._request_latencies[key]) > 1000:
            self._request_latencies[key] = self._request_latencies[key][-1000:]
        
        if status_code >= 400:
            self._error_counts[key] += 1
        
        # Record to metrics
        self.record(f"request_count_{endpoint}", self._request_counts[key], {"method": method})
        self.record(f"latency_{endpoint}", latency_ms, {"method": method})
    
    def get_system_metrics(self) -> SystemMetrics:
        """Get current system metrics"""
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        network = psutil.net_io_counters()
        
        return SystemMetrics(
            cpu_percent=psutil.cpu_percent(interval=0.1),
            memory_percent=memory.percent,
            memory_used_gb=memory.used / (1024 ** 3),
            memory_total_gb=memory.total / (1024 ** 3),
            disk_percent=disk.percent,
            disk_used_gb=disk.used / (1024 ** 3),
            disk_total_gb=disk.total / (1024 ** 3),
            network_sent_mb=network.bytes_sent / (1024 ** 2),
            network_recv_mb=network.bytes_recv / (1024 ** 2)
        )
    
    def collect_system_metrics(self):
        """Collect system metrics"""
        metrics = self.get_system_metrics()
        
        self.record("system.cpu", metrics.cpu_percent, {"unit": "percent"})
        self.record("system.memory", metrics.memory_percent, {"unit": "percent"})
        self.record("system.disk", metrics.disk_percent, {"unit": "percent"})
        self.record("system.network.sent", metrics.network_sent_mb, {"unit": "MB"})
        self.record("system.network.recv", metrics.network_recv_mb, {"unit": "MB"})
    
    async def start_monitoring(self, interval_seconds: int = 10):
        """Start background monitoring"""
        self._monitoring = True
        
        async def monitor_loop():
            while self._monitoring:
                try:
                    self.collect_system_metrics()
                    self.check_alerts()
                except Exception as e:
                    logger.error(f"Error collecting metrics: {e}")
                
                await asyncio.sleep(interval_seconds)
        
        self._monitor_task = asyncio.create_task(monitor_loop())
        logger.info(f"Started monitoring with {interval_seconds}s interval")
    
    def stop_monitoring(self):
        """Stop background monitoring"""
        self._monitoring = False
        if self._monitor_task:
            self._monitor_task.cancel()
        logger.info("Stopped monitoring")
    
    def get_metric_summary(
        self,
        metric_name: str,
        window_seconds: int = 300
    ) -> Dict[str, Any]:
        """Get metric summary for a time window"""
        if metric_name not in self.metrics:
            return {"error": "Metric not found"}
        
        metric = self.metrics[metric_name]
        cutoff = datetime.now() - timedelta(seconds=window_seconds)
        recent_points = [p for p in metric.points if p.timestamp > cutoff]
        
        if not recent_points:
            return {"count": 0}
        
        values = [p.value for p in recent_points]
        
        return {
            "name": metric_name,
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
            "latest": values[-1],
            "unit": metric.unit
        }
    
    def get_request_stats(
        self,
        endpoint: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get request statistics"""
        if endpoint:
            key = f"GET:{endpoint}" if ":" not in endpoint else endpoint
            count = self._request_counts.get(key, 0)
            latencies = self._request_latencies.get(key, [])
            errors = self._error_counts.get(key, 0)
            
            return {
                "endpoint": endpoint,
                "count": count,
                "errors": errors,
                "error_rate": errors / count if count > 0 else 0,
                "latency_avg_ms": sum(latencies) / len(latencies) if latencies else 0,
                "latency_p95_ms": sorted(latencies)[int(len(latencies) * 0.95)] if len(latencies) > 20 else (latencies[-1] if latencies else 0),
                "latency_p99_ms": sorted(latencies)[int(len(latencies) * 0.99)] if len(latencies) > 100 else (latencies[-1] if latencies else 0)
            }
        
        # All endpoints
        stats = []
        for key in self._request_counts:
            method, endpoint = key.split(":", 1) if ":" in key else ("GET", key)
            count = self._request_counts[key]
            latencies = self._request_latencies.get(key, [])
            errors = self._error_counts.get(key, 0)
            
            stats.append({
                "endpoint": endpoint,
                "method": method,
                "count": count,
                "errors": errors,
                "error_rate": errors / count if count > 0 else 0,
                "latency_avg_ms": sum(latencies) / len(latencies) if latencies else 0
            })
        
        return {"endpoints": stats}
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get data for monitoring dashboard"""
        system = self.get_system_metrics()
        
        metrics_summary = {}
        for name in self.metrics:
            metrics_summary[name] = self.get_metric_summary(name)
        
        request_stats = self.get_request_stats()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "system": {
                "cpu": system.cpu_percent,
                "memory": system.memory_percent,
                "disk": system.disk_percent,
                "network_sent_mb": system.network_sent_mb,
                "network_recv_mb": system.network_recv_mb
            },
            "metrics": metrics_summary,
            "requests": request_stats,
            "alerts": [
                {
                    "id": alert.id,
                    "rule": alert.rule_name,
                    "level": alert.level.value,
                    "message": alert.message,
                    "triggered_at": alert.triggered_at.isoformat()
                }
                for alert in self.active_alerts.values()
            ]
        }


class RequestTimingMiddleware:
    """Middleware to track request timing"""
    
    def __init__(self, monitor: PerformanceMonitor):
        self.monitor = monitor
    
    async def __call__(self, request, call_next):
        start_time = time.time()
        
        response = await call_next(request)
        
        duration_ms = (time.time() - start_time) * 1000
        
        self.monitor.record_request(
            endpoint=request.url.path,
            method=request.method,
            status_code=response.status_code,
            latency_ms=duration_ms
        )
        
        return response


# Global monitor instance
monitor = PerformanceMonitor()


def init_monitoring(app=None, enable_alerts: bool = True):
    """Initialize performance monitoring"""
    # Register default metrics
    monitor.register_metric("system.cpu", MetricType.CPU, "percent")
    monitor.register_metric("system.memory", MetricType.MEMORY, "percent")
    monitor.register_metric("system.disk", MetricType.DISK, "percent")
    
    # Add default alert rules
    if enable_alerts:
        monitor.add_alert_rule(AlertRule(
            name="High CPU Usage",
            metric="system.cpu",
            condition=">",
            threshold=80.0,
            duration_seconds=120,
            level=AlertLevel.WARNING
        ))
        
        monitor.add_alert_rule(AlertRule(
            name="High Memory Usage",
            metric="system.memory",
            condition=">",
            threshold=85.0,
            duration_seconds=120,
            level=AlertLevel.WARNING
        ))
        
        monitor.add_alert_rule(AlertRule(
            name="Critical Memory Usage",
            metric="system.memory",
            condition=">",
            threshold=95.0,
            duration_seconds=60,
            level=AlertLevel.CRITICAL
        ))
    
    if app:
        app.add_middleware(RequestTimingMiddleware, monitor=monitor)
    
    return monitor
