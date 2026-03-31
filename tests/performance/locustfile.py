"""AgentForge 性能测试 - Locust 测试脚本

测试场景:
- 健康检查: 1000 req/s 目标, P99 < 50ms
- 用户认证: 100 req/s 目标, P99 < 200ms
- API 查询: 500 req/s 目标, P99 < 100ms
- AI 生成: 20 req/s 目标, P99 < 5s
- 文件上传: 50 req/s 目标, P99 < 2s

运行方式:
    locust -f tests/performance/locustfile.py --host=http://localhost:8000
"""

import os
import json
import random
import string
from datetime import datetime

from locust import HttpUser, task, between, events
from locust.runners import MasterRunner, WorkerRunner


class AgentForgeUser(HttpUser):
    """AgentForge API 用户模拟"""

    wait_time = between(1, 3)

    def on_start(self):
        """用户开始时执行"""
        self.access_token = None
        self.refresh_token = None
        self.user_id = None

        self.username = f"test_user_{random.randint(10000, 99999)}"
        self.password = "TestPassword123!"

        self.login()

    def login(self):
        """登录获取 token"""
        response = self.client.post(
            "/api/v1/auth/token",
            data={
                "username": os.getenv("TEST_USERNAME", "admin"),
                "password": os.getenv("TEST_PASSWORD", "admin123")
            },
            name="/auth/token",
            catch_response=True
        )

        if response.status_code == 200:
            data = response.json()
            self.access_token = data.get("access_token")
            self.refresh_token = data.get("refresh_token")
            response.success()
        else:
            response.failure(f"登录失败: {response.status_code}")

    def get_headers(self):
        """获取认证头"""
        if self.access_token:
            return {"Authorization": f"Bearer {self.access_token}"}
        return {}

    @task(10)
    def health_check(self):
        """健康检查 - 高频任务"""
        self.client.get("/health", name="/health")

    @task(5)
    def get_current_user(self):
        """获取当前用户信息"""
        if not self.access_token:
            return

        self.client.get(
            "/api/v1/users/me",
            headers=self.get_headers(),
            name="/users/me"
        )

    @task(3)
    def list_orders(self):
        """列出订单"""
        if not self.access_token:
            return

        self.client.get(
            "/api/v1/fiverr/orders",
            headers=self.get_headers(),
            params={"limit": 20},
            name="/fiverr/orders"
        )

    @task(2)
    def search_knowledge(self):
        """搜索知识库"""
        if not self.access_token:
            return

        queries = ["Python", "Fiverr", "自动化", "AI", "项目交付"]
        query = random.choice(queries)

        self.client.post(
            "/api/v1/knowledge/search",
            headers=self.get_headers(),
            json={"query": query, "limit": 10},
            name="/knowledge/search"
        )

    @task(2)
    def list_files(self):
        """列出文件"""
        if not self.access_token:
            return

        self.client.get(
            "/api/v1/files",
            headers=self.get_headers(),
            params={"limit": 20},
            name="/files"
        )

    @task(1)
    def get_plugins(self):
        """获取插件列表"""
        if not self.access_token:
            return

        self.client.get(
            "/api/v1/plugins",
            headers=self.get_headers(),
            name="/plugins"
        )

    @task(1)
    def get_weather(self):
        """查询天气"""
        if not self.access_token:
            return

        cities = ["Beijing", "Shanghai", "Shenzhen", "Guangzhou", "Hangzhou"]
        city = random.choice(cities)

        self.client.post(
            "/api/v1/plugins/weather/query",
            headers=self.get_headers(),
            json={"city": city},
            name="/plugins/weather"
        )

    @task(1)
    def currency_convert(self):
        """货币转换"""
        if not self.access_token:
            return

        pairs = [
            ("USD", "CNY"),
            ("EUR", "CNY"),
            ("CNY", "USD"),
            ("GBP", "CNY")
        ]
        from_curr, to_curr = random.choice(pairs)

        self.client.post(
            "/api/v1/plugins/currency/convert",
            headers=self.get_headers(),
            json={
                "from": from_curr,
                "to": to_curr,
                "amount": random.randint(100, 10000)
            },
            name="/plugins/currency"
        )


class AIGenerationUser(HttpUser):
    """AI 生成 API 用户模拟"""

    wait_time = between(5, 10)

    def on_start(self):
        self.access_token = None
        self.login()

    def login(self):
        response = self.client.post(
            "/api/v1/auth/token",
            data={
                "username": os.getenv("TEST_USERNAME", "admin"),
                "password": os.getenv("TEST_PASSWORD", "admin123")
            },
            name="/auth/token",
            catch_response=True
        )

        if response.status_code == 200:
            data = response.json()
            self.access_token = data.get("access_token")
            response.success()

    def get_headers(self):
        if self.access_token:
            return {"Authorization": f"Bearer {self.access_token}"}
        return {}

    @task(3)
    def generate_content(self):
        """生成内容"""
        if not self.access_token:
            return

        prompts = [
            "为一个 Fiverr Python 编程服务写一段吸引人的描述",
            "写一封客户感谢邮件",
            "生成一个项目交付报告模板",
            "创建一个社交媒体推广文案"
        ]
        prompt = random.choice(prompts)

        self.client.post(
            "/api/v1/ai/generate",
            headers=self.get_headers(),
            json={
                "prompt": prompt,
                "task_type": "content_generation"
            },
            name="/ai/generate",
            timeout=30
        )

    @task(1)
    def analyze_sentiment(self):
        """情感分析"""
        if not self.access_token:
            return

        texts = [
            "Great service, fast delivery!",
            "非常满意这次合作",
            "The quality could be better",
            "Excellent work, will order again"
        ]
        text = random.choice(texts)

        self.client.post(
            "/api/v1/ai/sentiment",
            headers=self.get_headers(),
            json={"text": text},
            name="/ai/sentiment"
        )


class FileUploadUser(HttpUser):
    """文件上传用户模拟"""

    wait_time = between(3, 8)

    def on_start(self):
        self.access_token = None
        self.login()

    def login(self):
        response = self.client.post(
            "/api/v1/auth/token",
            data={
                "username": os.getenv("TEST_USERNAME", "admin"),
                "password": os.getenv("TEST_PASSWORD", "admin123")
            },
            name="/auth/token",
            catch_response=True
        )

        if response.status_code == 200:
            data = response.json()
            self.access_token = data.get("access_token")
            response.success()

    def get_headers(self):
        if self.access_token:
            return {"Authorization": f"Bearer {self.access_token}"}
        return {}

    @task(2)
    def upload_small_file(self):
        """上传小文件 (< 100KB)"""
        if not self.access_token:
            return

        content = "".join(random.choices(string.ascii_letters + string.digits, k=50000))
        files = {"file": ("test.txt", content.encode(), "text/plain")}

        self.client.post(
            "/api/v1/files/upload",
            headers={"Authorization": f"Bearer {self.access_token}"},
            files=files,
            name="/files/upload [small]"
        )

    @task(1)
    def upload_medium_file(self):
        """上传中等文件 (100KB - 1MB)"""
        if not self.access_token:
            return

        content = "".join(random.choices(string.ascii_letters + string.digits, k=500000))
        files = {"file": ("test_medium.txt", content.encode(), "text/plain")}

        self.client.post(
            "/api/v1/files/upload",
            headers={"Authorization": f"Bearer {self.access_token}"},
            files=files,
            name="/files/upload [medium]"
        )


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """测试开始时执行"""
    print("\n" + "=" * 60)
    print("AgentForge 性能测试开始")
    print(f"时间: {datetime.now().isoformat()}")
    print(f"目标主机: {environment.host}")
    print("=" * 60 + "\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """测试结束时执行"""
    print("\n" + "=" * 60)
    print("AgentForge 性能测试结束")
    print(f"时间: {datetime.now().isoformat()}")
    print("=" * 60 + "\n")


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """请求完成时记录"""
    if exception:
        print(f"[ERROR] {name}: {exception}")
    elif response_time > 1000:
        print(f"[SLOW] {name}: {response_time:.0f}ms")
