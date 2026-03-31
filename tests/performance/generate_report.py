"""性能测试报告生成器"""

import os
import json
import re
from datetime import datetime
from pathlib import Path


class ReportGenerator:
    """报告生成器"""

    def __init__(self, report_dir: str = "tests/performance/reports"):
        self.report_dir = Path(report_dir)
        self.report_dir.mkdir(parents=True, exist_ok=True)

    def parse_locust_stats(self) -> dict:
        """解析 Locust 统计数据"""
        stats_file = self.report_dir / "locust_stats_stats.csv"

        if not stats_file.exists():
            return {}

        stats = {}
        with open(stats_file, 'r') as f:
            lines = f.readlines()
            if len(lines) > 1:
                headers = lines[0].strip().split(',')
                for line in lines[1:]:
                    values = line.strip().split(',')
                    if len(values) >= len(headers):
                        row = dict(zip(headers, values))
                        name = row.get('Name', row.get('Type', 'unknown'))
                        stats[name] = {
                            "request_count": int(row.get('Request Count', 0)),
                            "failure_count": int(row.get('Failure Count', 0)),
                            "median_response_time": float(row.get('Median Response Time', 0)),
                            "average_response_time": float(row.get('Average Response Time', 0)),
                            "min_response_time": float(row.get('Min Response Time', 0)),
                            "max_response_time": float(row.get('Max Response Time', 0)),
                            "average_content_size": float(row.get('Average Content Size', 0)),
                            "requests_per_sec": float(row.get('Requests/s', 0)),
                            "failures_per_sec": float(row.get('Failures/s', 0)),
                            "p50": float(row.get('50%', 0)),
                            "p66": float(row.get('66%', 0)),
                            "p75": float(row.get('75%', 0)),
                            "p80": float(row.get('80%', 0)),
                            "p90": float(row.get('90%', 0)),
                            "p95": float(row.get('95%', 0)),
                            "p98": float(row.get('98%', 0)),
                            "p99": float(row.get('99%', 0)),
                            "p100": float(row.get('100%', 0))
                        }

        return stats

    def parse_db_log(self) -> dict:
        """解析数据库性能日志"""
        log_file = self.report_dir / "db_performance.log"

        if not log_file.exists():
            return {}

        results: dict[str, dict[str, float]] = {}
        current_test = None

        with open(log_file, 'r') as f:
            for line in f:
                if line.startswith("运行:"):
                    match = re.search(r"运行: (.+) \(", line)
                    if match:
                        current_test = match.group(1)
                        results[current_test] = {}

                elif current_test and ":" in line:
                    match = re.search(r"(\w+):\s*([\d.]+)", line)
                    if match:
                        key = match.group(1)
                        value = float(match.group(2))
                        results[current_test][key] = value

        return results

    def check_thresholds(self, locust_stats: dict, db_stats: dict) -> dict:
        """检查性能阈值"""
        issues = []

        thresholds = {
            "/health": {"max_p99_ms": 50, "target_rps": 1000},
            "/auth/token": {"max_p99_ms": 200, "target_rps": 100},
            "/users/me": {"max_p99_ms": 100, "target_rps": 500},
            "/fiverr/orders": {"max_p99_ms": 100, "target_rps": 500},
            "/knowledge/search": {"max_p99_ms": 200, "target_rps": 100},
            "/ai/generate": {"max_p99_ms": 5000, "target_rps": 20},
        }

        for endpoint, threshold in thresholds.items():
            if endpoint in locust_stats:
                stats = locust_stats[endpoint]
                p99 = stats.get("p99", 0)
                rps = stats.get("requests_per_sec", 0)

                if p99 > threshold["max_p99_ms"]:
                    issues.append({
                        "endpoint": endpoint,
                        "issue": "P99 响应时间超标",
                        "actual": f"{p99:.1f}ms",
                        "threshold": f"{threshold['max_p99_ms']}ms"
                    })

                if rps < threshold["target_rps"] * 0.8:
                    issues.append({
                        "endpoint": endpoint,
                        "issue": "RPS 低于目标",
                        "actual": f"{rps:.1f}",
                        "threshold": f"{threshold['target_rps']}"
                    })

        return issues

    def generate_html_report(self, locust_stats: dict, db_stats: dict, issues: list) -> str:
        """生成 HTML 报告"""
        html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AgentForge 性能测试报告</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 20px;
        }}
        .header h1 {{
            margin: 0;
            font-size: 28px;
        }}
        .header p {{
            margin: 10px 0 0;
            opacity: 0.9;
        }}
        .section {{
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .section h2 {{
            margin-top: 0;
            color: #333;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 10px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }}
        th {{
            background: #f8f9fa;
            font-weight: 600;
        }}
        tr:hover {{
            background: #f8f9fa;
        }}
        .good {{
            color: #10b981;
            font-weight: 600;
        }}
        .warning {{
            color: #f59e0b;
            font-weight: 600;
        }}
        .bad {{
            color: #ef4444;
            font-weight: 600;
        }}
        .issue {{
            background: #fef2f2;
            border-left: 4px solid #ef4444;
            padding: 10px 15px;
            margin: 10px 0;
            border-radius: 0 5px 5px 0;
        }}
        .metric {{
            display: inline-block;
            padding: 5px 10px;
            border-radius: 5px;
            font-size: 14px;
            margin: 2px;
        }}
        .metric-good {{
            background: #d1fae5;
            color: #065f46;
        }}
        .metric-warning {{
            background: #fef3c7;
            color: #92400e;
        }}
        .metric-bad {{
            background: #fee2e2;
            color: #991b1b;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .summary-card {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }}
        .summary-card .value {{
            font-size: 24px;
            font-weight: 700;
            color: #667eea;
        }}
        .summary-card .label {{
            font-size: 14px;
            color: #666;
            margin-top: 5px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 AgentForge 性能测试报告</h1>
        <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>

    <div class="section">
        <h2>📊 测试概览</h2>
        <div class="summary">
            <div class="summary-card">
                <div class="value">{len(locust_stats)}</div>
                <div class="label">API 端点测试</div>
            </div>
            <div class="summary-card">
                <div class="value">{len(db_stats)}</div>
                <div class="label">数据库测试</div>
            </div>
            <div class="summary-card">
                <div class="value">{len(issues)}</div>
                <div class="label">性能问题</div>
            </div>
            <div class="summary-card">
                <div class="value">{sum(s.get('request_count', 0) for s in locust_stats.values())}</div>
                <div class="label">总请求数</div>
            </div>
        </div>
    </div>
"""

        if issues:
            html += """
    <div class="section">
        <h2>⚠️ 性能问题</h2>
"""
            for issue in issues:
                html += f"""
        <div class="issue">
            <strong>{issue['endpoint']}</strong>: {issue['issue']}<br>
            实际值: {issue['actual']} | 阈值: {issue['threshold']}
        </div>
"""
            html += "    </div>"

        html += """
    <div class="section">
        <h2>🌐 API 性能详情</h2>
        <table>
            <tr>
                <th>端点</th>
                <th>请求数</th>
                <th>失败数</th>
                <th>RPS</th>
                <th>平均响应</th>
                <th>P50</th>
                <th>P95</th>
                <th>P99</th>
            </tr>
"""
        for endpoint, stats in locust_stats.items():
            p99 = stats.get('p99', 0)
            p99_class = 'good' if p99 < 100 else ('warning' if p99 < 500 else 'bad')

            html += f"""
            <tr>
                <td><code>{endpoint}</code></td>
                <td>{stats.get('request_count', 0):,}</td>
                <td class="{'bad' if stats.get('failure_count', 0) > 0 else 'good'}">{stats.get('failure_count', 0)}</td>
                <td>{stats.get('requests_per_sec', 0):.1f}</td>
                <td>{stats.get('average_response_time', 0):.1f}ms</td>
                <td>{stats.get('p50', 0):.1f}ms</td>
                <td>{stats.get('p95', 0):.1f}ms</td>
                <td class="{p99_class}">{p99:.1f}ms</td>
            </tr>
"""

        html += """
        </table>
    </div>

    <div class="section">
        <h2>💾 数据库性能详情</h2>
        <table>
            <tr>
                <th>测试项</th>
                <th>迭代次数</th>
                <th>平均耗时</th>
                <th>P50</th>
                <th>P95</th>
                <th>P99</th>
                <th>成功率</th>
            </tr>
"""
        for test_name, stats in db_stats.items():
            p99 = stats.get('P99', 0)
            p99_class = 'good' if p99 < 50 else ('warning' if p99 < 100 else 'bad')

            html += f"""
            <tr>
                <td>{test_name}</td>
                <td>{stats.get('迭代次数', 'N/A')}</td>
                <td>{stats.get('平均耗时', 0):.2f}ms</td>
                <td>{stats.get('P50', 0):.2f}ms</td>
                <td>{stats.get('P95', 0):.2f}ms</td>
                <td class="{p99_class}">{p99:.2f}ms</td>
                <td class="{'good' if stats.get('成功率', 0) == 100 else 'warning'}">{stats.get('成功率', 0):.1f}%</td>
            </tr>
"""

        html += """
        </table>
    </div>

    <div class="section">
        <h2>📝 测试配置</h2>
        <ul>
            <li>并发用户数: 100</li>
            <li>生成速率: 10 用户/秒</li>
            <li>测试时长: 3 分钟</li>
            <li>数据库测试数据量: 100,000 条</li>
        </ul>
    </div>

    <div class="section">
        <h2>📄 详细报告</h2>
        <ul>
            <li><a href="locust_report.html">Locust HTML 报告</a></li>
            <li><a href="locust_output.log">Locust 输出日志</a></li>
            <li><a href="db_performance.log">数据库性能日志</a></li>
        </ul>
    </div>
</body>
</html>
"""
        return html

    def generate(self):
        """生成完整报告"""
        print("解析 Locust 统计数据...")
        locust_stats = self.parse_locust_stats()

        print("解析数据库性能日志...")
        db_stats = self.parse_db_log()

        print("检查性能阈值...")
        issues = self.check_thresholds(locust_stats, db_stats)

        print("生成 HTML 报告...")
        html = self.generate_html_report(locust_stats, db_stats, issues)

        report_path = self.report_dir / "summary_report.html"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"报告已生成: {report_path}")

        return {
            "locust_stats": locust_stats,
            "db_stats": db_stats,
            "issues": issues,
            "report_path": str(report_path)
        }


def main():
    generator = ReportGenerator()
    result = generator.generate()

    if result["issues"]:
        print(f"\n发现 {len(result['issues'])} 个性能问题:")
        for issue in result["issues"]:
            print(f"  - {issue['endpoint']}: {issue['issue']}")
    else:
        print("\n所有性能指标达标!")


if __name__ == "__main__":
    main()
