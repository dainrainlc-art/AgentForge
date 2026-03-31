"""数据库性能测试脚本

测试场景:
- 订单查询: 10万条数据, < 50ms
- 全文搜索: 10万条数据, < 100ms
- 批量写入: 1000条/批, < 1s
"""

import asyncio
import time
import random
import string
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List, Dict, Any
import statistics

import asyncpg
import redis.asyncio as redis


@dataclass
class TestResult:
    """测试结果"""
    name: str
    iterations: int
    total_time: float
    min_time: float
    max_time: float
    avg_time: float
    p50_time: float
    p95_time: float
    p99_time: float
    errors: int
    success_rate: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "iterations": self.iterations,
            "total_time": round(self.total_time, 3),
            "min_time": round(self.min_time, 3),
            "max_time": round(self.max_time, 3),
            "avg_time": round(self.avg_time, 3),
            "p50_time": round(self.p50_time, 3),
            "p95_time": round(self.p95_time, 3),
            "p99_time": round(self.p99_time, 3),
            "errors": self.errors,
            "success_rate": round(self.success_rate, 2)
        }

    def __str__(self) -> str:
        return (
            f"\n{self.name}\n"
            f"  迭代次数: {self.iterations}\n"
            f"  总耗时: {self.total_time:.3f}s\n"
            f"  平均耗时: {self.avg_time:.3f}ms\n"
            f"  P50: {self.p50_time:.3f}ms\n"
            f"  P95: {self.p95_time:.3f}ms\n"
            f"  P99: {self.p99_time:.3f}ms\n"
            f"  错误数: {self.errors}\n"
            f"  成功率: {self.success_rate:.2f}%"
        )


class DatabasePerformanceTest:
    """数据库性能测试"""

    def __init__(
        self,
        postgres_dsn: str = "postgresql://agentforge:agentforge@localhost:5432/agentforge",
        redis_url: str = "redis://localhost:6379"
    ):
        self.postgres_dsn = postgres_dsn
        self.redis_url = redis_url
        self.pg_pool = None
        self.redis_client = None

    async def setup(self):
        """初始化连接"""
        self.pg_pool = await asyncpg.create_pool(
            self.postgres_dsn,
            min_size=5,
            max_size=20
        )
        self.redis_client = redis.from_url(self.redis_url)
        print("数据库连接初始化完成")

    async def teardown(self):
        """关闭连接"""
        if self.pg_pool:
            await self.pg_pool.close()
        if self.redis_client:
            await self.redis_client.close()
        print("数据库连接已关闭")

    async def prepare_test_data(self, count: int = 100000):
        """准备测试数据"""
        print(f"准备 {count} 条测试数据...")

        async with self.pg_pool.acquire() as conn:
            await conn.execute("DROP TABLE IF EXISTS perf_test_orders")
            await conn.execute("""
                CREATE TABLE perf_test_orders (
                    id SERIAL PRIMARY KEY,
                    order_id VARCHAR(50) NOT NULL,
                    customer_name VARCHAR(200),
                    status VARCHAR(50),
                    amount DECIMAL(10, 2),
                    description TEXT,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            """)

            batch_size = 1000
            for i in range(0, count, batch_size):
                batch = []
                for j in range(min(batch_size, count - i)):
                    order_id = f"ORD-{random.randint(100000, 999999)}"
                    customer_name = f"Customer_{random.randint(1, 10000)}"
                    status = random.choice(["pending", "in_progress", "completed", "cancelled"])
                    amount = random.uniform(10, 1000)
                    description = "".join(random.choices(string.ascii_letters + " ", k=200))

                    batch.append((order_id, customer_name, status, amount, description))

                await conn.executemany(
                    "INSERT INTO perf_test_orders (order_id, customer_name, status, amount, description) VALUES ($1, $2, $3, $4, $5)",
                    batch
                )

                if (i + batch_size) % 10000 == 0:
                    print(f"  已插入 {i + batch_size} 条数据")

            await conn.execute("CREATE INDEX idx_perf_orders_status ON perf_test_orders(status)")
            await conn.execute("CREATE INDEX idx_perf_orders_created ON perf_test_orders(created_at)")

        print(f"测试数据准备完成: {count} 条")

    def calculate_percentile(self, data: List[float], percentile: float) -> float:
        """计算百分位数"""
        if not data:
            return 0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]

    async def run_test(
        self,
        name: str,
        test_func,
        iterations: int = 100
    ) -> TestResult:
        """运行测试"""
        times = []
        errors = 0

        for _ in range(iterations):
            try:
                start = time.perf_counter()
                await test_func()
                end = time.perf_counter()
                times.append((end - start) * 1000)
            except Exception as e:
                errors += 1
                print(f"  错误: {e}")

        if not times:
            return TestResult(
                name=name,
                iterations=iterations,
                total_time=0,
                min_time=0,
                max_time=0,
                avg_time=0,
                p50_time=0,
                p95_time=0,
                p99_time=0,
                errors=errors,
                success_rate=0
            )

        return TestResult(
            name=name,
            iterations=iterations,
            total_time=sum(times) / 1000,
            min_time=min(times),
            max_time=max(times),
            avg_time=statistics.mean(times),
            p50_time=self.calculate_percentile(times, 50),
            p95_time=self.calculate_percentile(times, 95),
            p99_time=self.calculate_percentile(times, 99),
            errors=errors,
            success_rate=(iterations - errors) / iterations * 100
        )

    async def test_simple_query(self):
        """简单查询测试"""
        async with self.pg_pool.acquire() as conn:
            await conn.fetch("SELECT * FROM perf_test_orders LIMIT 10")

    async def test_indexed_query(self):
        """索引查询测试"""
        async with self.pg_pool.acquire() as conn:
            status = random.choice(["pending", "in_progress", "completed", "cancelled"])
            await conn.fetch(
                "SELECT * FROM perf_test_orders WHERE status = $1 LIMIT 100",
                status
            )

    async def test_range_query(self):
        """范围查询测试"""
        async with self.pg_pool.acquire() as conn:
            start_date = datetime.now() - timedelta(days=random.randint(1, 30))
            end_date = start_date + timedelta(days=7)
            await conn.fetch(
                "SELECT * FROM perf_test_orders WHERE created_at BETWEEN $1 AND $2 LIMIT 100",
                start_date,
                end_date
            )

    async def test_aggregation_query(self):
        """聚合查询测试"""
        async with self.pg_pool.acquire() as conn:
            await conn.fetch("""
                SELECT status, COUNT(*) as count, AVG(amount) as avg_amount
                FROM perf_test_orders
                GROUP BY status
            """)

    async def test_full_text_search(self):
        """全文搜索测试"""
        async with self.pg_pool.acquire() as conn:
            search_term = f"Customer_{random.randint(1, 10000)}"
            await conn.fetch(
                "SELECT * FROM perf_test_orders WHERE customer_name LIKE $1 LIMIT 100",
                f"%{search_term}%"
            )

    async def test_join_query(self):
        """连接查询测试"""
        async with self.pg_pool.acquire() as conn:
            await conn.fetch("""
                SELECT o.*, 
                       COUNT(*) OVER (PARTITION BY o.status) as status_count
                FROM perf_test_orders o
                WHERE o.amount > $1
                LIMIT 100
            """, random.uniform(100, 500))

    async def test_insert(self):
        """插入测试"""
        async with self.pg_pool.acquire() as conn:
            order_id = f"TEST-{random.randint(100000, 999999)}"
            await conn.execute(
                """
                INSERT INTO perf_test_orders (order_id, customer_name, status, amount, description)
                VALUES ($1, $2, $3, $4, $5)
                """,
                order_id,
                f"TestCustomer_{random.randint(1, 1000)}",
                "pending",
                random.uniform(10, 100),
                "Test description"
            )

    async def test_update(self):
        """更新测试"""
        async with self.pg_pool.acquire() as conn:
            result = await conn.fetchrow("SELECT id FROM perf_test_orders ORDER BY RANDOM() LIMIT 1")
            if result:
                await conn.execute(
                    "UPDATE perf_test_orders SET status = $1, updated_at = NOW() WHERE id = $2",
                    random.choice(["pending", "in_progress", "completed"]),
                    result["id"]
                )

    async def test_batch_insert(self):
        """批量插入测试"""
        batch = []
        for _ in range(1000):
            batch.append((
                f"BATCH-{random.randint(100000, 999999)}",
                f"BatchCustomer_{random.randint(1, 1000)}",
                "pending",
                random.uniform(10, 100),
                "Batch test description"
            ))

        async with self.pg_pool.acquire() as conn:
            await conn.executemany(
                """
                INSERT INTO perf_test_orders (order_id, customer_name, status, amount, description)
                VALUES ($1, $2, $3, $4, $5)
                """,
                batch
            )

    async def test_redis_get(self):
        """Redis GET 测试"""
        key = f"test_key_{random.randint(1, 10000)}"
        await self.redis_client.get(key)

    async def test_redis_set(self):
        """Redis SET 测试"""
        key = f"test_key_{random.randint(1, 10000)}"
        value = "".join(random.choices(string.ascii_letters, k=100))
        await self.redis_client.set(key, value, ex=60)

    async def test_redis_incr(self):
        """Redis INCR 测试"""
        key = "test_counter"
        await self.redis_client.incr(key)

    async def test_redis_hash(self):
        """Redis Hash 操作测试"""
        key = f"test_hash_{random.randint(1, 1000)}"
        field = f"field_{random.randint(1, 100)}"
        value = "".join(random.choices(string.ascii_letters, k=50))
        await self.redis_client.hset(key, field, value)

    async def run_all_tests(self) -> Dict[str, Any]:
        """运行所有测试"""
        results = []

        print("\n" + "=" * 60)
        print("开始数据库性能测试")
        print("=" * 60)

        postgres_tests = [
            ("简单查询", self.test_simple_query, 500),
            ("索引查询", self.test_indexed_query, 500),
            ("范围查询", self.test_range_query, 200),
            ("聚合查询", self.test_aggregation_query, 100),
            ("全文搜索", self.test_full_text_search, 200),
            ("连接查询", self.test_join_query, 100),
            ("单条插入", self.test_insert, 200),
            ("单条更新", self.test_update, 200),
            ("批量插入 (1000条)", self.test_batch_insert, 10),
        ]

        for name, test_func, iterations in postgres_tests:
            print(f"\n运行: {name} ({iterations} 次)...")
            result = await self.run_test(name, test_func, iterations)
            results.append(result)
            print(result)

        redis_tests = [
            ("Redis GET", self.test_redis_get, 1000),
            ("Redis SET", self.test_redis_set, 1000),
            ("Redis INCR", self.test_redis_incr, 1000),
            ("Redis HSET", self.test_redis_hash, 1000),
        ]

        for name, test_func, iterations in redis_tests:
            print(f"\n运行: {name} ({iterations} 次)...")
            result = await self.run_test(name, test_func, iterations)
            results.append(result)
            print(result)

        return {
            "test_time": datetime.now().isoformat(),
            "results": [r.to_dict() for r in results]
        }


async def main():
    test = DatabasePerformanceTest()

    try:
        await test.setup()
        await test.prepare_test_data(100000)
        results = await test.run_all_tests()

        print("\n" + "=" * 60)
        print("测试完成!")
        print("=" * 60)

        return results
    finally:
        await test.teardown()


if __name__ == "__main__":
    asyncio.run(main())
