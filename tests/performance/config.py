"""性能测试配置"""

import os

TEST_CONFIG = {
    "target_host": os.getenv("TARGET_HOST", "http://localhost:8000"),
    "test_username": os.getenv("TEST_USERNAME", "admin"),
    "test_password": os.getenv("TEST_PASSWORD", "admin123"),

    "locust": {
        "users": 100,
        "spawn_rate": 10,
        "run_time": "5m",
        "headless": True,
        "html_report": "tests/performance/reports/locust_report.html",
        "csv_prefix": "tests/performance/reports/locust_stats"
    },

    "database": {
        "postgres_dsn": os.getenv(
            "DATABASE_URL",
            "postgresql://agentforge:agentforge@localhost:5432/agentforge"
        ),
        "redis_url": os.getenv("REDIS_URL", "redis://localhost:6379"),
        "test_data_count": 100000
    },

    "thresholds": {
        "health_check": {
            "target_rps": 1000,
            "max_p99_ms": 50
        },
        "auth": {
            "target_rps": 100,
            "max_p99_ms": 200
        },
        "api_query": {
            "target_rps": 500,
            "max_p99_ms": 100
        },
        "ai_generation": {
            "target_rps": 20,
            "max_p99_ms": 5000
        },
        "file_upload": {
            "target_rps": 50,
            "max_p99_ms": 2000
        },
        "db_query": {
            "max_p99_ms": 50
        },
        "db_search": {
            "max_p99_ms": 100
        },
        "db_batch_insert": {
            "max_time_ms": 1000
        }
    }
}
