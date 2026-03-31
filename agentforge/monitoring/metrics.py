"""
Monitoring Module - Prometheus metrics and Grafana dashboards
"""
from prometheus_client import Counter, Histogram, Gauge, Info
from typing import Dict, Any
import time
import asyncio
from loguru import logger


REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint'],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0]
)

ACTIVE_REQUESTS = Gauge(
    'http_requests_in_progress',
    'Number of HTTP requests in progress',
    ['method', 'endpoint']
)

DATABASE_CONNECTIONS = Gauge(
    'database_connections_active',
    'Number of active database connections'
)

DATABASE_QUERY_LATENCY = Histogram(
    'database_query_duration_seconds',
    'Database query latency',
    ['operation'],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0]
)

CACHE_HITS = Counter(
    'cache_hits_total',
    'Total cache hits',
    ['cache_type']
)

CACHE_MISSES = Counter(
    'cache_misses_total',
    'Total cache misses',
    ['cache_type']
)

LLM_REQUESTS = Counter(
    'llm_requests_total',
    'Total LLM API requests',
    ['model', 'status']
)

LLM_TOKENS_USED = Counter(
    'llm_tokens_used_total',
    'Total tokens used',
    ['model', 'type']
)

LLM_LATENCY = Histogram(
    'llm_request_duration_seconds',
    'LLM request latency',
    ['model'],
    buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0]
)

BACKUP_COUNT = Gauge(
    'backup_total_count',
    'Total number of backups'
)

BACKUP_SIZE = Gauge(
    'backup_size_bytes',
    'Total backup size in bytes'
)

BACKUP_LAST_TIMESTAMP = Gauge(
    'backup_last_timestamp',
    'Timestamp of last backup'
)

SYSTEM_INFO = Info(
    'agentforge_system',
    'System information'
)


class MetricsCollector:
    """Collect and expose metrics"""
    
    def __init__(self):
        self._start_time = time.time()
    
    def record_request(
        self,
        method: str,
        endpoint: str,
        status: int,
        duration: float
    ) -> None:
        """Record HTTP request metrics"""
        REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status).inc()
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(duration)
    
    def start_request(self, method: str, endpoint: str) -> None:
        """Mark request as started"""
        ACTIVE_REQUESTS.labels(method=method, endpoint=endpoint).inc()
    
    def end_request(self, method: str, endpoint: str) -> None:
        """Mark request as ended"""
        ACTIVE_REQUESTS.labels(method=method, endpoint=endpoint).dec()
    
    def record_db_query(
        self,
        operation: str,
        duration: float
    ) -> None:
        """Record database query metrics"""
        DATABASE_QUERY_LATENCY.labels(operation=operation).observe(duration)
    
    def set_db_connections(self, count: int) -> None:
        """Set active database connections"""
        DATABASE_CONNECTIONS.set(count)
    
    def record_cache_hit(self, cache_type: str) -> None:
        """Record cache hit"""
        CACHE_HITS.labels(cache_type=cache_type).inc()
    
    def record_cache_miss(self, cache_type: str) -> None:
        """Record cache miss"""
        CACHE_MISSES.labels(cache_type=cache_type).inc()
    
    def record_llm_request(
        self,
        model: str,
        status: str,
        duration: float,
        prompt_tokens: int = 0,
        completion_tokens: int = 0
    ) -> None:
        """Record LLM request metrics"""
        LLM_REQUESTS.labels(model=model, status=status).inc()
        LLM_LATENCY.labels(model=model).observe(duration)
        
        if prompt_tokens > 0:
            LLM_TOKENS_USED.labels(model=model, type='prompt').inc(prompt_tokens)
        if completion_tokens > 0:
            LLM_TOKENS_USED.labels(model=model, type='completion').inc(completion_tokens)
    
    def update_backup_metrics(
        self,
        count: int,
        total_size: int,
        last_timestamp: float
    ) -> None:
        """Update backup metrics"""
        BACKUP_COUNT.set(count)
        BACKUP_SIZE.set(total_size)
        BACKUP_LAST_TIMESTAMP.set(last_timestamp)
    
    def set_system_info(
        self,
        version: str,
        environment: str,
        python_version: str
    ) -> None:
        """Set system information"""
        SYSTEM_INFO.info({
            'version': version,
            'environment': environment,
            'python_version': python_version,
            'uptime': str(time.time() - self._start_time)
        })
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics summary"""
        return {
            "uptime_seconds": time.time() - self._start_time,
            "timestamp": time.time()
        }


metrics_collector = MetricsCollector()


GRAFANA_DASHBOARD = {
    "dashboard": {
        "title": "AgentForge Monitoring",
        "tags": ["agentforge", "ai"],
        "timezone": "browser",
        "panels": [
            {
                "title": "Request Rate",
                "type": "graph",
                "targets": [
                    {
                        "expr": "rate(http_requests_total[5m])",
                        "legendFormat": "{{method}} {{endpoint}}"
                    }
                ],
                "gridPos": {"x": 0, "y": 0, "w": 12, "h": 8}
            },
            {
                "title": "Request Latency",
                "type": "graph",
                "targets": [
                    {
                        "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
                        "legendFormat": "p95 latency"
                    },
                    {
                        "expr": "histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))",
                        "legendFormat": "p99 latency"
                    }
                ],
                "gridPos": {"x": 12, "y": 0, "w": 12, "h": 8}
            },
            {
                "title": "Active Requests",
                "type": "gauge",
                "targets": [
                    {
                        "expr": "sum(http_requests_in_progress)",
                        "legendFormat": "Active"
                    }
                ],
                "gridPos": {"x": 0, "y": 8, "w": 6, "h": 4}
            },
            {
                "title": "Database Connections",
                "type": "gauge",
                "targets": [
                    {
                        "expr": "database_connections_active",
                        "legendFormat": "Connections"
                    }
                ],
                "gridPos": {"x": 6, "y": 8, "w": 6, "h": 4}
            },
            {
                "title": "Cache Hit Rate",
                "type": "graph",
                "targets": [
                    {
                        "expr": "rate(cache_hits_total[5m]) / (rate(cache_hits_total[5m]) + rate(cache_misses_total[5m])) * 100",
                        "legendFormat": "Hit Rate %"
                    }
                ],
                "gridPos": {"x": 12, "y": 8, "w": 12, "h": 8}
            },
            {
                "title": "LLM Requests",
                "type": "graph",
                "targets": [
                    {
                        "expr": "rate(llm_requests_total[5m])",
                        "legendFormat": "{{model}}"
                    }
                ],
                "gridPos": {"x": 0, "y": 16, "w": 12, "h": 8}
            },
            {
                "title": "LLM Latency",
                "type": "graph",
                "targets": [
                    {
                        "expr": "histogram_quantile(0.95, rate(llm_request_duration_seconds_bucket[5m]))",
                        "legendFormat": "p95 latency"
                    }
                ],
                "gridPos": {"x": 12, "y": 16, "w": 12, "h": 8}
            },
            {
                "title": "Token Usage",
                "type": "graph",
                "targets": [
                    {
                        "expr": "rate(llm_tokens_used_total[1h])",
                        "legendFormat": "{{model}} - {{type}}"
                    }
                ],
                "gridPos": {"x": 0, "y": 24, "w": 24, "h": 8}
            }
        ]
    }
}


PROMETHEUS_ALERTING_RULES = """
groups:
  - name: agentforge_alerts
    rules:
      - alert: HighRequestLatency
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: High request latency detected
          description: "95th percentile latency is above 1 second"

      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: High error rate detected
          description: "Error rate is above 5%"

      - alert: DatabaseConnectionPoolExhausted
        expr: database_connections_active > 90
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: Database connection pool nearly exhausted
          description: "Active connections above 90"

      - alert: LowCacheHitRate
        expr: rate(cache_hits_total[5m]) / (rate(cache_hits_total[5m]) + rate(cache_misses_total[5m])) < 0.5
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: Low cache hit rate
          description: "Cache hit rate below 50%"

      - alert: LLMLatencyHigh
        expr: histogram_quantile(0.95, rate(llm_request_duration_seconds_bucket[5m])) > 30
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: LLM latency is high
          description: "95th percentile LLM latency above 30 seconds"

      - alert: LLMErrorRate
        expr: rate(llm_requests_total{status="error"}[5m]) / rate(llm_requests_total[5m]) > 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: High LLM error rate
          description: "LLM error rate above 10%"

      - alert: BackupNotRun
        expr: time() - backup_last_timestamp > 86400
        for: 1h
        labels:
          severity: warning
        annotations:
          summary: Backup not run in 24 hours
          description: "Last backup was more than 24 hours ago"

      - alert: HighMemoryUsage
        expr: process_resident_memory_bytes / (1024 * 1024 * 1024) > 4
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: High memory usage
          description: "Memory usage above 4GB"
"""


def get_grafana_dashboard_json() -> Dict[str, Any]:
    """Get Grafana dashboard configuration"""
    return GRAFANA_DASHBOARD


def get_prometheus_rules() -> str:
    """Get Prometheus alerting rules"""
    return PROMETHEUS_ALERTING_RULES
