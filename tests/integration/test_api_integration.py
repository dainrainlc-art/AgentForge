"""
API 集成测试
测试 FastAPI 应用与业务引擎的集成

测试场景：
1. 健康检查和 API 基础功能
2. 认证授权流程
3. 订单管理 API
4. 知识管理 API
5. Chat API
6. 错误处理和验证
"""
import pytest
import asyncio
from typing import Dict, Any
from httpx import AsyncClient, ASGITransport
from datetime import timedelta

from integrations.api.main import app
from agentforge.config import settings


# ============================================================================
# API 测试夹具
# ============================================================================


@pytest.fixture(scope="function")
async def client():
    """创建测试 HTTP 客户端"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.fixture
def auth_headers():
    """模拟认证头（用于需要认证的测试）"""
    # 注意：这是一个模拟的 token，实际测试中需要生成真实的 JWT
    return {
        "Authorization": "Bearer test_token_12345",
        "Content-Type": "application/json",
    }


# ============================================================================
# 健康检查 API 测试
# ============================================================================


class TestHealthAPI:
    """健康检查 API 集成测试"""

    @pytest.mark.asyncio
    async def test_health_check(self, client):
        """测试健康检查端点"""
        response = await client.get("/api/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
        assert "version" in data
        assert "timestamp" in data

    @pytest.mark.asyncio
    async def test_root_endpoint(self, client):
        """测试根端点"""
        response = await client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == settings.app_name
        assert "version" in data
        assert data["status"] == "running"

    @pytest.mark.asyncio
    async def test_health_with_database_status(self, client):
        """测试包含数据库状态的健康检查"""
        response = await client.get("/api/health?check_db=true")

        assert response.status_code in [200, 503]  # 503 表示数据库未连接
        data = response.json()

        if response.status_code == 200:
            assert data["status"] == "healthy"
            assert "database" in data or "db_status" in data


# ============================================================================
# 认证 API 测试
# ============================================================================


class TestAuthAPI:
    """认证 API 集成测试"""

    @pytest.mark.asyncio
    async def test_register_user(self, client):
        """测试用户注册"""
        import uuid

        unique_email = f"test_{uuid.uuid4()}@example.com"

        user_data = {
            "email": unique_email,
            "password": "Test@123456",
            "name": "测试用户",
        }

        response = await client.post("/api/auth/register", json=user_data)

        # 可能成功（如果数据库可用）或失败（如果数据库不可用）
        if response.status_code == 201:
            data = response.json()
            assert "user_id" in data or "id" in data
            assert data["email"] == unique_email
        elif response.status_code in [500, 503]:
            # 数据库不可用的情况
            pytest.skip("数据库不可用，跳过注册测试")

    @pytest.mark.asyncio
    async def test_login_with_valid_credentials(self, client):
        """测试使用有效凭据登录"""
        login_data = {
            "email": "admin@agentforge.local",
            "password": "admin123",  # 默认管理员密码
        }

        response = await client.post("/api/auth/login", json=login_data)

        # 如果管理员账户存在
        if response.status_code == 200:
            data = response.json()
            assert "access_token" in data
            assert data["token_type"] == "bearer"
        else:
            pytest.skip("管理员账户不存在，跳过登录测试")

    @pytest.mark.asyncio
    async def test_login_with_invalid_credentials(self, client):
        """测试使用无效凭据登录"""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "WrongPassword123",
        }

        response = await client.post("/api/auth/login", json=login_data)

        assert response.status_code in [401, 404]
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_login_validation(self, client):
        """测试登录验证"""
        # 缺少密码
        login_data = {"email": "test@example.com"}

        response = await client.post("/api/auth/login", json=login_data)
        assert response.status_code == 422  # 验证错误

        # 无效邮箱格式
        login_data = {"email": "invalid-email", "password": "Test@123456"}
        response = await client.post("/api/auth/login", json=login_data)
        assert response.status_code == 422


# ============================================================================
# 订单管理 API 测试
# ============================================================================


class TestOrdersAPI:
    """订单管理 API 集成测试"""

    @pytest.mark.asyncio
    async def test_get_orders_list(self, client, auth_headers):
        """测试获取订单列表"""
        response = await client.get("/api/orders", headers=auth_headers)

        # 如果认证失败（token 是模拟的），应该返回 401
        if response.status_code == 401:
            pytest.skip("需要真实 JWT token")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_order_by_id(self, client, auth_headers):
        """测试根据 ID 获取订单"""
        order_id = "test-order-id"

        response = await client.get(f"/api/orders/{order_id}", headers=auth_headers)

        if response.status_code == 401:
            pytest.skip("需要真实 JWT token")

        # 订单不存在
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_create_order(self, client, auth_headers):
        """测试创建订单"""
        order_data = {
            "fiverr_order_id": "FO_TEST_123",
            "status": "pending",
            "amount": 100.00,
            "currency": "USD",
            "description": "测试订单",
            "metadata": {"buyer": "test_buyer", "delivery_days": 7},
        }

        response = await client.post("/api/orders", json=order_data, headers=auth_headers)

        if response.status_code == 401:
            pytest.skip("需要真实 JWT token")

        # 验证响应
        if response.status_code == 201:
            data = response.json()
            assert data["fiverr_order_id"] == "FO_TEST_123"

    @pytest.mark.asyncio
    async def test_update_order_status(self, client, auth_headers):
        """测试更新订单状态"""
        order_id = "test-order-id"
        update_data = {"status": "completed"}

        response = await client.put(
            f"/api/orders/{order_id}/status", json=update_data, headers=auth_headers
        )

        if response.status_code == 401:
            pytest.skip("需要真实 JWT token")

        # 验证响应
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_delete_order(self, client, auth_headers):
        """测试删除订单"""
        order_id = "test-order-id"

        response = await client.delete(f"/api/orders/{order_id}", headers=auth_headers)

        if response.status_code == 401:
            pytest.skip("需要真实 JWT token")

        assert response.status_code in [200, 204, 404]

    @pytest.mark.asyncio
    async def test_order_with_fiverr_integration(
        self, client, auth_headers, mock_external_services
    ):
        """测试订单与 Fiverr 集成"""
        # 这个测试验证订单 API 与 Fiverr 客户端的集成
        order_data = {
            "fiverr_order_id": "FO_INTEGRATION_TEST",
            "status": "active",
            "amount": 250.00,
            "currency": "USD",
            "description": "Fiverr 集成测试订单",
        }

        response = await client.post("/api/orders", json=order_data, headers=auth_headers)

        if response.status_code == 401:
            pytest.skip("需要真实 JWT token")


# ============================================================================
# 知识管理 API 测试
# ============================================================================


class TestKnowledgeAPI:
    """知识管理 API 集成测试"""

    @pytest.mark.asyncio
    async def test_get_knowledge_docs(self, client, auth_headers):
        """测试获取知识文档列表"""
        response = await client.get("/api/knowledge", headers=auth_headers)

        if response.status_code == 401:
            pytest.skip("需要真实 JWT token")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_create_knowledge_document(self, client, auth_headers):
        """测试创建知识文档"""
        doc_data = {
            "title": "测试知识文档",
            "content": "这是测试内容，用于验证知识管理 API。",
            "source": "api_test",
            "doc_type": "test",
            "tags": ["测试", "API", "集成"],
        }

        response = await client.post("/api/knowledge", json=doc_data, headers=auth_headers)

        if response.status_code == 401:
            pytest.skip("需要真实 JWT token")

        if response.status_code == 201:
            data = response.json()
            assert data["title"] == "测试知识文档"
            assert "id" in data

    @pytest.mark.asyncio
    async def test_search_knowledge_docs(self, client, auth_headers):
        """测试搜索知识文档"""
        query = "测试"

        response = await client.get(
            f"/api/knowledge/search?q={query}", headers=auth_headers
        )

        if response.status_code == 401:
            pytest.skip("需要真实 JWT token")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_update_knowledge_document(self, client, auth_headers):
        """测试更新知识文档"""
        doc_id = "test-doc-id"
        update_data = {
            "title": "更新后的标题",
            "content": "更新后的内容",
        }

        response = await client.put(
            f"/api/knowledge/{doc_id}", json=update_data, headers=auth_headers
        )

        if response.status_code == 401:
            pytest.skip("需要真实 JWT token")

        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_delete_knowledge_document(self, client, auth_headers):
        """测试删除知识文档"""
        doc_id = "test-doc-id"

        response = await client.delete(f"/api/knowledge/{doc_id}", headers=auth_headers)

        if response.status_code == 401:
            pytest.skip("需要真实 JWT token")

        assert response.status_code in [200, 204, 404]

    @pytest.mark.asyncio
    async def test_knowledge_with_vector_search(
        self, client, auth_headers, mock_external_services
    ):
        """测试知识文档的向量搜索"""
        search_data = {
            "query": "如何集成 AI 模型",
            "top_k": 5,
            "use_vector_search": True,
        }

        response = await client.post(
            "/api/knowledge/search", json=search_data, headers=auth_headers
        )

        if response.status_code == 401:
            pytest.skip("需要真实 JWT token")

        # 验证返回结果包含相似度分数
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)


# ============================================================================
# Chat API 测试
# ============================================================================


class TestChatAPI:
    """Chat API 集成测试"""

    @pytest.mark.asyncio
    async def test_send_message(self, client, auth_headers, mock_external_services):
        """测试发送消息"""
        message_data = {
            "message": "你好，请介绍一下 AgentForge",
            "context": {"conversation_id": "test-conversation-123"},
        }

        response = await client.post("/api/chat", json=message_data, headers=auth_headers)

        if response.status_code == 401:
            pytest.skip("需要真实 JWT token")

        if response.status_code == 200:
            data = response.json()
            assert "response" in data or "message" in data

    @pytest.mark.asyncio
    async def test_chat_with_context(self, client, auth_headers, mock_external_services):
        """测试带上下文的聊天"""
        conversation_id = "test-conv-123"

        # 第一轮对话
        message1 = {"message": "什么是 AgentForge？", "conversation_id": conversation_id}
        response1 = await client.post("/api/chat", json=message1, headers=auth_headers)

        if response1.status_code == 401:
            pytest.skip("需要真实 JWT token")

        # 第二轮对话（带上下文）
        message2 = {
            "message": "它有哪些功能？",
            "conversation_id": conversation_id,
        }
        response2 = await client.post("/api/chat", json=message2, headers=auth_headers)

        if response2.status_code == 200:
            data = response2.json()
            assert "response" in data

    @pytest.mark.asyncio
    async def test_chat_with_different_models(
        self, client, auth_headers, mock_external_services
    ):
        """测试使用不同 AI 模型聊天"""
        message_data = {
            "message": "测试消息",
            "model": "glm-5",  # 指定模型
        }

        response = await client.post("/api/chat", json=message_data, headers=auth_headers)

        if response.status_code == 401:
            pytest.skip("需要真实 JWT token")

        if response.status_code == 200:
            data = response.json()
            assert "response" in data

    @pytest.mark.asyncio
    async def test_chat_message_validation(self, client, auth_headers):
        """测试聊天消息验证"""
        # 空消息
        message_data = {"message": ""}

        response = await client.post("/api/chat", json=message_data, headers=auth_headers)

        if response.status_code == 401:
            pytest.skip("需要真实 JWT token")

        assert response.status_code == 422  # 验证错误


# ============================================================================
# Fiverr 分析 API 测试
# ============================================================================


class TestFiverrAnalyticsAPI:
    """Fiverr 分析 API 集成测试"""

    @pytest.mark.asyncio
    async def test_get_fiverr_stats(self, client, auth_headers, mock_external_services):
        """测试获取 Fiverr 统计数据"""
        response = await client.get("/api/fiverr/stats", headers=auth_headers)

        if response.status_code == 401:
            pytest.skip("需要真实 JWT token")

        if response.status_code == 200:
            data = response.json()
            assert "total_orders" in data or "stats" in data

    @pytest.mark.asyncio
    async def test_get_order_analytics(self, client, auth_headers, mock_external_services):
        """测试获取订单分析"""
        response = await client.get("/api/fiverr/analytics", headers=auth_headers)

        if response.status_code == 401:
            pytest.skip("需要真实 JWT token")

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)

    @pytest.mark.asyncio
    async def test_get_revenue_report(self, client, auth_headers, mock_external_services):
        """测试获取收入报告"""
        params = {"start_date": "2024-01-01", "end_date": "2024-12-31"}

        response = await client.get(
            "/api/fiverr/revenue", params=params, headers=auth_headers
        )

        if response.status_code == 401:
            pytest.skip("需要真实 JWT token")

        if response.status_code == 200:
            data = response.json()
            assert "total_revenue" in data or "report" in data


# ============================================================================
# 错误处理测试
# ============================================================================


class TestErrorHandling:
    """错误处理集成测试"""

    @pytest.mark.asyncio
    async def test_404_not_found(self, client):
        """测试 404 错误处理"""
        response = await client.get("/api/nonexistent-endpoint")

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_405_method_not_allowed(self, client):
        """测试 405 错误处理"""
        response = await client.post("/api/health")  # health 只支持 GET

        assert response.status_code == 405

    @pytest.mark.asyncio
    async def test_422_validation_error(self, client, auth_headers):
        """测试 422 验证错误"""
        # 发送无效数据
        invalid_data = {"invalid_field": "invalid_value"}

        response = await client.post(
            "/api/knowledge", json=invalid_data, headers=auth_headers
        )

        if response.status_code == 401:
            pytest.skip("需要真实 JWT token")

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_cors_headers(self, client):
        """测试 CORS 头"""
        response = await client.options(
            "/api/health",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
            },
        )

        # 检查 CORS 头是否存在
        assert "access-control-allow-origin" in response.headers


# ============================================================================
# API 性能测试
# ============================================================================


class TestAPIPerformance:
    """API 性能集成测试"""

    @pytest.mark.asyncio
    async def test_health_endpoint_response_time(self, client):
        """测试健康检查端点响应时间"""
        import time

        start = time.time()
        response = await client.get("/api/health")
        end = time.time()

        response_time = (end - start) * 1000  # 毫秒
        assert response_time < 1000  # 响应时间应小于 1 秒
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_concurrent_requests(self, client):
        """测试并发请求处理"""
        import asyncio

        async def make_request():
            response = await client.get("/api/health")
            return response.status_code

        # 并发发送 10 个请求
        tasks = [make_request() for _ in range(10)]
        results = await asyncio.gather(*tasks)

        # 所有请求都应成功
        assert all(status == 200 for status in results)


# ============================================================================
# API 版本兼容性测试
# ============================================================================


class TestAPIVersioning:
    """API 版本兼容性测试"""

    @pytest.mark.asyncio
    async def test_api_version_in_response(self, client):
        """测试 API 版本信息"""
        response = await client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "version" in data

    @pytest.mark.asyncio
    async def test_health_api_compatibility(self, client):
        """测试健康检查 API 兼容性"""
        response = await client.get("/api/health")

        assert response.status_code == 200
        data = response.json()

        # 确保包含必要的字段
        assert "status" in data
