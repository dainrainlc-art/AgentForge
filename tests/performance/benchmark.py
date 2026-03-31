"""
Performance Benchmark Tests
"""
import time
import asyncio
import statistics
from typing import List, Callable
from concurrent.futures import ThreadPoolExecutor
import httpx
from locust import HttpUser, task, between


class APIPerformanceTest:
    """API Performance Testing"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results = []
    
    async def benchmark_endpoint(
        self,
        endpoint: str,
        method: str = "GET",
        data: dict = None,
        iterations: int = 100,
        concurrency: int = 10
    ) -> dict:
        """Benchmark an API endpoint"""
        
        async def make_request(client: httpx.AsyncClient) -> float:
            start = time.time()
            try:
                if method == "GET":
                    response = await client.get(f"{self.base_url}{endpoint}")
                else:
                    response = await client.post(
                        f"{self.base_url}{endpoint}",
                        json=data
                    )
                response.raise_for_status()
                return time.time() - start
            except Exception as e:
                print(f"Request failed: {e}")
                return None
        
        async with httpx.AsyncClient() as client:
            tasks = []
            for _ in range(iterations):
                tasks.append(make_request(client))
            
            results = await asyncio.gather(*tasks)
            valid_results = [r for r in results if r is not None]
            
            if not valid_results:
                return {"error": "All requests failed"}
            
            return {
                "endpoint": endpoint,
                "iterations": iterations,
                "successful": len(valid_results),
                "failed": iterations - len(valid_results),
                "min_time": min(valid_results) * 1000,
                "max_time": max(valid_results) * 1000,
                "avg_time": statistics.mean(valid_results) * 1000,
                "median_time": statistics.median(valid_results) * 1000,
                "p95_time": sorted(valid_results)[int(len(valid_results) * 0.95)] * 1000,
                "p99_time": sorted(valid_results)[int(len(valid_results) * 0.99)] * 1000,
            }
    
    async def run_all_benchmarks(self) -> List[dict]:
        """Run all benchmark tests"""
        benchmarks = [
            ("/api/health", "GET", None),
            ("/", "GET", None),
            ("/api/chat", "POST", {"message": "Hello", "session_id": "test"}),
        ]
        
        results = []
        for endpoint, method, data in benchmarks:
            print(f"Benchmarking {endpoint}...")
            result = await self.benchmark_endpoint(endpoint, method, data)
            results.append(result)
            print(f"  Avg: {result.get('avg_time', 0):.2f}ms")
        
        return results


class DatabasePerformanceTest:
    """Database Performance Testing"""
    
    def __init__(self):
        self.results = []
    
    async def benchmark_query(
        self,
        query_func: Callable,
        iterations: int = 100
    ) -> dict:
        """Benchmark a database query"""
        times = []
        
        for _ in range(iterations):
            start = time.time()
            await query_func()
            times.append(time.time() - start)
        
        return {
            "iterations": iterations,
            "min_time": min(times) * 1000,
            "max_time": max(times) * 1000,
            "avg_time": statistics.mean(times) * 1000,
            "median_time": statistics.median(times) * 1000,
        }


class CachePerformanceTest:
    """Cache Performance Testing"""
    
    def __init__(self):
        self.results = []
    
    async def benchmark_cache_operations(
        self,
        cache_manager,
        iterations: int = 1000
    ) -> dict:
        """Benchmark cache get/set operations"""
        
        # Benchmark set
        set_times = []
        for i in range(iterations):
            start = time.time()
            await cache_manager.set(f"key_{i}", {"data": f"value_{i}"})
            set_times.append(time.time() - start)
        
        # Benchmark get
        get_times = []
        for i in range(iterations):
            start = time.time()
            await cache_manager.get(f"key_{i}")
            get_times.append(time.time() - start)
        
        return {
            "iterations": iterations,
            "set_avg": statistics.mean(set_times) * 1000,
            "get_avg": statistics.mean(get_times) * 1000,
            "set_min": min(set_times) * 1000,
            "get_min": min(get_times) * 1000,
            "set_max": max(set_times) * 1000,
            "get_max": max(get_times) * 1000,
        }


# Locust load testing
class AgentForgeUser(HttpUser):
    """Locust user for load testing"""
    
    wait_time = between(1, 3)
    
    @task(3)
    def health_check(self):
        """Test health endpoint"""
        self.client.get("/api/health")
    
    @task(2)
    def get_root(self):
        """Test root endpoint"""
        self.client.get("/")
    
    @task(1)
    def chat(self):
        """Test chat endpoint"""
        self.client.post("/api/chat", json={
            "message": "Hello",
            "session_id": "load_test"
        })


async def main():
    """Run all performance tests"""
    print("=" * 60)
    print("AgentForge Performance Benchmark")
    print("=" * 60)
    
    # API Performance
    print("\n1. API Performance Tests")
    print("-" * 60)
    api_test = APIPerformanceTest()
    api_results = await api_test.run_all_benchmarks()
    
    for result in api_results:
        print(f"\nEndpoint: {result['endpoint']}")
        print(f"  Success Rate: {result['successful']}/{result['iterations']}")
        print(f"  Avg Response Time: {result['avg_time']:.2f}ms")
        print(f"  P95: {result['p95_time']:.2f}ms")
        print(f"  P99: {result['p99_time']:.2f}ms")
    
    print("\n" + "=" * 60)
    print("Benchmark Complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
