"""
集成测试配置和基础夹具
提供数据库、API、工作流等集成测试所需的基础设施
"""
import os
import pytest
import asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock, patch

# 设置测试环境变量
os.environ["TESTING"] = "true"
os.environ["POSTGRES_DB"] = "agentforge_test"
os.environ["POSTGRES_USER"] = "agentforge"
os.environ["POSTGRES_PASSWORD"] = "test_password"
os.environ["REDIS_PORT"] = "6379"
os.environ["QDRANT_PORT"] = "6333"
os.environ["N8N_PORT"] = "5678"


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环用于异步测试"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_db_config():
    """测试数据库配置"""
    return {
        "host": "localhost",
        "port": 5432,
        "database": "agentforge_test",
        "user": "agentforge",
        "password": "test_password",
    }


@pytest.fixture(scope="session")
def test_redis_config():
    """测试 Redis 配置"""
    return {
        "host": "localhost",
        "port": 6379,
        "db": 0,
    }


@pytest.fixture(scope="session")
def test_qdrant_config():
    """测试 Qdrant 配置"""
    return {
        "host": "localhost",
        "port": 6333,
    }


@pytest.fixture
def mock_qianfan_response():
    """模拟百度千帆 API 响应"""
    return {
        "result": "这是一个模拟的 AI 响应",
        "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
    }


@pytest.fixture
def mock_n8n_workflow_response():
    """模拟 N8N 工作流执行响应"""
    return {
        "id": "test-execution-123",
        "status": "success",
        "data": {"result": "工作流执行成功"},
    }


@pytest.fixture
def sample_order_data():
    """示例订单数据"""
    return {
        "fiverr_order_id": "FO123456789",
        "status": "active",
        "amount": 150.00,
        "currency": "USD",
        "description": "网站开发服务",
        "metadata": {
            "buyer": "test_buyer",
            "delivery_days": 7,
            "requirements": "需要一个现代化的网站",
        },
    }


@pytest.fixture
def sample_knowledge_doc():
    """示例知识文档"""
    return {
        "title": "测试文档标题",
        "content": "这是一个测试知识文档的内容，用于验证知识管理功能。",
        "source": "test_source",
        "doc_type": "general",
        "tags": ["测试", "集成", "知识管理"],
    }


@pytest.fixture
def sample_user_data():
    """示例用户数据"""
    return {
        "email": "testuser@example.com",
        "password": "Test@123456",
        "name": "测试用户",
    }


@pytest.fixture
def mock_external_services():
    """模拟外部服务（用于隔离测试）"""
    with patch("agentforge.llm.qianfan_client.QianfanClient") as mock_qianfan, patch(
        "integrations.external.n8n_client.N8NClient"
    ) as mock_n8n:
        # 配置千帆 mock
        qianfan_instance = AsyncMock()
        qianfan_instance.generate_text = AsyncMock(
            return_value={"result": "模拟的 AI 响应", "usage": {"total_tokens": 30}}
        )
        mock_qianfan.return_value = qianfan_instance

        # 配置 N8N mock
        n8n_instance = AsyncMock()
        n8n_instance.execute_workflow = AsyncMock(
            return_value={"execution_id": "test-123", "status": "success"}
        )
        n8n_instance.get_workflow_status = AsyncMock(return_value={"status": "completed"})
        mock_n8n.return_value = n8n_instance

        yield {
            "qianfan": mock_qianfan,
            "n8n": mock_n8n,
        }
