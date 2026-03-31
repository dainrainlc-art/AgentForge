"""性能测试模块

提供 API 性能测试、数据库性能测试和报告生成功能。
"""

from .config import TEST_CONFIG
from .generate_report import ReportGenerator
from .optimizations import PERFORMANCE_OPTIMIZATIONS, get_optimization_recommendations

__all__ = [
    "TEST_CONFIG",
    "ReportGenerator",
    "PERFORMANCE_OPTIMIZATIONS",
    "get_optimization_recommendations"
]
