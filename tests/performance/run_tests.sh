#!/bin/bash
# AgentForge 性能测试运行脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
REPORT_DIR="$PROJECT_ROOT/tests/performance/reports"

echo "========================================"
echo "AgentForge 性能测试"
echo "========================================"

mkdir -p "$REPORT_DIR"

cd "$PROJECT_ROOT"

echo ""
echo "检查依赖..."
pip install locust asyncpg redis --quiet

echo ""
echo "检查服务状态..."
curl -s http://localhost:8000/health > /dev/null || {
    echo "错误: API 服务未运行"
    echo "请先启动服务: docker-compose up -d"
    exit 1
}

echo ""
echo "========================================"
echo "1. API 性能测试 (Locust)"
echo "========================================"

echo "运行 Locust 测试..."
locust -f tests/performance/locustfile.py \
    --host=http://localhost:8000 \
    --users 100 \
    --spawn-rate 10 \
    --run-time 3m \
    --headless \
    --html "$REPORT_DIR/locust_report.html" \
    --csv "$REPORT_DIR/locust_stats" \
    2>&1 | tee "$REPORT_DIR/locust_output.log"

echo ""
echo "========================================"
echo "2. 数据库性能测试"
echo "========================================"

echo "运行数据库测试..."
python tests/performance/db_performance.py 2>&1 | tee "$REPORT_DIR/db_performance.log"

echo ""
echo "========================================"
echo "3. 生成测试报告"
echo "========================================"

python tests/performance/generate_report.py

echo ""
echo "========================================"
echo "测试完成!"
echo "========================================"
echo ""
echo "报告位置: $REPORT_DIR"
echo "  - locust_report.html  (API 性能报告)"
echo "  - db_performance.log  (数据库性能日志)"
echo "  - summary_report.html (综合报告)"
echo ""
