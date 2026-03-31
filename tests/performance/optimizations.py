"""性能优化建议

基于性能测试结果，提供针对性的优化建议。
"""

PERFORMANCE_OPTIMIZATIONS = {
    "database": {
        "connection_pool": {
            "issue": "数据库连接池配置不足",
            "solution": "增加连接池大小和超时配置",
            "code": """
# config.py
DATABASE_CONFIG = {
    "min_pool_size": 10,
    "max_pool_size": 50,
    "connection_timeout": 30,
    "command_timeout": 60
}
"""
        },
        "indexing": {
            "issue": "缺少必要的索引",
            "solution": "为常用查询字段添加索引",
            "sql": """
-- 订单表索引
CREATE INDEX idx_orders_status_created ON orders(status, created_at);
CREATE INDEX idx_orders_customer ON orders(customer_id);

-- 知识库索引
CREATE INDEX idx_knowledge_tags ON knowledge_docs USING GIN(tags);
CREATE INDEX idx_knowledge_content ON knowledge_docs USING GIN(to_tsvector('english', content));
"""
        },
        "query_optimization": {
            "issue": "N+1 查询问题",
            "solution": "使用 JOIN 和预加载优化查询",
            "code": """
# 使用 JOIN 替代多次查询
async def get_orders_with_details(order_ids: List[str]):
    query = '''
        SELECT o.*, c.name as customer_name, d.delivery_status
        FROM orders o
        LEFT JOIN customers c ON o.customer_id = c.id
        LEFT JOIN deliveries d ON o.id = d.order_id
        WHERE o.id = ANY($1)
    '''
    return await conn.fetch(query, order_ids)
"""
        }
    },

    "api": {
        "caching": {
            "issue": "频繁访问相同数据",
            "solution": "实现多级缓存策略",
            "code": """
# cache_manager.py
class MultiLevelCache:
    def __init__(self):
        self.local_cache = LRUCache(maxsize=1000)
        self.redis = redis.Redis()

    async def get(self, key: str):
        # L1: 本地缓存
        if key in self.local_cache:
            return self.local_cache[key]

        # L2: Redis 缓存
        value = await self.redis.get(key)
        if value:
            self.local_cache[key] = value
            return value

        return None

    async def set(self, key: str, value: Any, ttl: int = 300):
        self.local_cache[key] = value
        await self.redis.setex(key, ttl, json.dumps(value))
"""
        },
        "compression": {
            "issue": "响应数据体积过大",
            "solution": "启用 Gzip 压缩",
            "code": """
# main.py
from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(
    GZipMiddleware,
    minimum_size=1000,
    compresslevel=6
)
"""
        },
        "batch_requests": {
            "issue": "大量小请求",
            "solution": "实现批量请求接口",
            "code": """
# 批量查询接口
@router.post("/orders/batch")
async def get_orders_batch(order_ids: List[str]):
    return await order_service.get_by_ids(order_ids)

# 批量创建接口
@router.post("/orders/batch-create")
async def create_orders_batch(orders: List[OrderCreate]):
    return await order_service.create_batch(orders)
"""
        }
    },

    "async": {
        "issue": "同步阻塞操作",
        "solution": "使用异步处理",
        "code": """
# 异步文件处理
async def process_file(file_path: Path):
    async with aiofiles.open(file_path, 'rb') as f:
        content = await f.read()
    return await process_content(content)

# 异步 HTTP 请求
async def fetch_multiple_urls(urls: List[str]):
    async with httpx.AsyncClient() as client:
        tasks = [client.get(url) for url in urls]
        return await asyncio.gather(*tasks)
"""
    },

    "rate_limiting": {
        "issue": "API 过载",
        "solution": "实现速率限制",
        "code": """
# rate_limiter.py
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter

@app.on_event("startup")
async def startup():
    redis = redis.Redis()
    await FastAPILimiter.init(redis)

@router.get("/api/endpoint", dependencies=[Depends(RateLimiter(times=100, seconds=60))])
async def endpoint():
    return {"status": "ok"}
"""
    },

    "background_tasks": {
        "issue": "耗时操作阻塞响应",
        "solution": "使用后台任务",
        "code": """
from fastapi import BackgroundTasks

@router.post("/reports/generate")
async def generate_report(
    background_tasks: BackgroundTasks,
    report_type: str
):
    background_tasks.add_task(create_report, report_type)
    return {"status": "processing", "message": "报告生成中..."}

async def create_report(report_type: str):
    # 耗时操作
    await asyncio.sleep(10)
    # 生成报告...
"""
    }
}


def get_optimization_recommendations(test_results: dict) -> list:
    """根据测试结果生成优化建议"""
    recommendations = []

    for endpoint, stats in test_results.get("locust_stats", {}).items():
        p99 = stats.get("p99", 0)
        rps = stats.get("requests_per_sec", 0)

        if p99 > 500:
            recommendations.append({
                "priority": "high",
                "endpoint": endpoint,
                "issue": f"P99 响应时间过高 ({p99:.0f}ms)",
                "recommendations": [
                    "检查数据库查询是否有 N+1 问题",
                    "添加适当的缓存策略",
                    "考虑使用异步处理"
                ]
            })

        if rps < 50:
            recommendations.append({
                "priority": "medium",
                "endpoint": endpoint,
                "issue": f"RPS 较低 ({rps:.1f})",
                "recommendations": [
                    "检查是否有阻塞操作",
                    "优化数据库查询",
                    "增加连接池大小"
                ]
            })

    return recommendations
