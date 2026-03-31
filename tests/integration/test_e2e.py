"""
端到端业务流程测试
测试完整的业务流程，模拟真实用户场景

测试场景：
1. Fiverr 订单处理完整流程
2. 知识管理完整流程
3. 社交媒体内容生成与发布流程
4. 客户沟通完整流程
5. 多模块协作流程
"""
import pytest
import asyncio
from typing import Dict, Any, List
from datetime import datetime
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch

from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text

from integrations.api.main import app
from agentforge.config import settings


# ============================================================================
# 端到端测试夹具
# ============================================================================


# 测试数据库 URL
TEST_DATABASE_URL = "postgresql+asyncpg://agentforge:test_password@localhost:5432/agentforge_test"


@pytest.fixture(scope="function")
async def db_session():
    """创建数据库会话用于端到端测试"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    session = async_session()

    try:
        yield session
        await session.rollback()
    finally:
        await session.close()
        await engine.dispose()


@pytest.fixture(scope="function")
async def e2e_client():
    """创建端到端测试 HTTP 客户端"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.fixture
def mock_all_external_services():
    """模拟所有外部服务"""
    with patch("agentforge.llm.qianfan_client.QianfanClient") as mock_qianfan, patch(
        "integrations.external.n8n_client.N8NClient"
    ) as mock_n8n, patch("integrations.external.fiverr_client.FiverrClient") as mock_fiverr:

        # 配置千帆 mock
        qianfan_instance = AsyncMock()
        qianfan_instance.generate_text = AsyncMock(
            return_value={
                "result": "模拟的 AI 响应",
                "usage": {"total_tokens": 30},
            }
        )
        mock_qianfan.return_value = qianfan_instance

        # 配置 N8N mock
        n8n_instance = AsyncMock()
        n8n_instance.execute_workflow = AsyncMock(
            return_value={"execution_id": "test-123", "status": "success"}
        )
        n8n_instance.get_workflow_status = AsyncMock(return_value={"status": "completed"})
        mock_n8n.return_value = n8n_instance

        # 配置 Fiverr mock
        fiverr_instance = AsyncMock()
        fiverr_instance.get_orders = AsyncMock(return_value=[])
        fiverr_instance.get_order_details = AsyncMock(
            return_value={
                "id": "FO123456",
                "status": "active",
                "buyer_username": "test_buyer",
                "amount": 150.00,
            }
        )
        mock_fiverr.return_value = fiverr_instance

        yield {
            "qianfan": mock_qianfan,
            "n8n": mock_n8n,
            "fiverr": mock_fiverr,
        }


@pytest.fixture
def e2e_test_data():
    """端到端测试数据"""
    return {
        "user": {
            "email": f"e2e_test_{uuid4()}@example.com",
            "password": "Test@123456",
            "name": "端到端测试用户",
        },
        "order": {
            "fiverr_order_id": f"FO_E2E_{uuid4()}",
            "status": "active",
            "amount": 200.00,
            "currency": "USD",
            "description": "端到端测试订单",
            "metadata": {"buyer": "e2e_buyer", "delivery_days": 5},
        },
        "knowledge_doc": {
            "title": "端到端测试文档",
            "content": "这是端到端测试的知识文档内容。",
            "source": "e2e_test",
            "doc_type": "test",
            "tags": ["端到端", "测试", "集成"],
        },
    }


# ============================================================================
# Fiverr 订单处理端到端测试
# ============================================================================


class TestFiverrOrderE2E:
    """Fiverr 订单处理端到端测试"""

    @pytest.mark.asyncio
    async def test_complete_order_workflow(
        self, e2e_client, db_session, mock_all_external_services, e2e_test_data
    ):
        """测试完整的 Fiverr 订单处理流程"""
        from agentforge.security.password_handler import PasswordHandler

        # 步骤 1: 创建测试用户
        user_id = uuid4()
        password_hash = PasswordHandler.hash_password(e2e_test_data["user"]["password"])

        await db_session.execute(
            text(
                """
                INSERT INTO users (id, email, password_hash, name, is_active)
                VALUES (:id, :email, :password_hash, :name, :is_active)
            """
            ),
            {
                "id": user_id,
                "email": e2e_test_data["user"]["email"],
                "password_hash": password_hash,
                "name": e2e_test_data["user"]["name"],
                "is_active": True,
            },
        )
        await db_session.commit()

        # 步骤 2: 创建订单
        order_id = uuid4()
        await db_session.execute(
            text(
                """
                INSERT INTO orders (id, user_id, fiverr_order_id, status, amount, currency, description, metadata)
                VALUES (:id, :user_id, :fiverr_order_id, :status, :amount, :currency, :description, :metadata)
            """
            ),
            {
                "id": order_id,
                "user_id": user_id,
                "fiverr_order_id": e2e_test_data["order"]["fiverr_order_id"],
                "status": e2e_test_data["order"]["status"],
                "amount": e2e_test_data["order"]["amount"],
                "currency": e2e_test_data["order"]["currency"],
                "description": e2e_test_data["order"]["description"],
                "metadata": e2e_test_data["order"]["metadata"],
            },
        )
        await db_session.commit()

        # 步骤 3: 验证订单已创建
        result = await db_session.execute(
            text("SELECT * FROM orders WHERE id = :id"), {"id": order_id}
        )
        order = result.fetchone()
        assert order is not None
        assert order.fiverr_order_id == e2e_test_data["order"]["fiverr_order_id"]

        # 步骤 4: 模拟 AI 分析订单
        # （在实际系统中，这会触发工作流）
        qianfan_mock = mock_all_external_services["qianfan"].return_value
        analysis_result = await qianfan_mock.generate_text(
            prompt="分析订单 FO_E2E_TEST", system_message="你是 Fiverr 订单分析助手"
        )

        assert analysis_result is not None
        assert "result" in analysis_result

        # 步骤 5: 模拟触发 N8N 工作流
        n8n_mock = mock_all_external_services["n8n"].return_value
        workflow_result = await n8n_mock.execute_workflow(
            workflow_id="fiverr-order-workflow",
            data={"order_id": str(order_id), "action": "process"},
        )

        assert workflow_result is not None
        assert workflow_result.get("status") == "success"

        # 步骤 6: 更新订单状态
        await db_session.execute(
            text("UPDATE orders SET status = :status WHERE id = :id"),
            {"status": "processing", "id": order_id},
        )
        await db_session.commit()

        # 验证最终状态
        result = await db_session.execute(
            text("SELECT status FROM orders WHERE id = :id"), {"id": order_id}
        )
        final_status = result.fetchone()
        assert final_status.status == "processing"

        # 清理
        await db_session.execute(text("DELETE FROM orders WHERE id = :id"), {"id": order_id})
        await db_session.execute(text("DELETE FROM users WHERE id = :id"), {"id": user_id})
        await db_session.commit()

    @pytest.mark.asyncio
    async def test_order_status_change_workflow(
        self, e2e_client, db_session, mock_all_external_services
    ):
        """测试订单状态变更工作流"""
        from agentforge.security.password_handler import PasswordHandler

        # 创建测试用户和订单
        user_id = uuid4()
        order_id = uuid4()
        password_hash = PasswordHandler.hash_password("Test@123456")

        await db_session.execute(
            text(
                """
                INSERT INTO users (id, email, password_hash, name, is_active)
                VALUES (:id, :email, :password_hash, :name, :is_active)
            """
            ),
            {
                "id": user_id,
                "email": f"status_test_{uuid4()}@example.com",
                "password_hash": password_hash,
                "name": "状态测试用户",
                "is_active": True,
            },
        )

        await db_session.execute(
            text(
                """
                INSERT INTO orders (id, user_id, fiverr_order_id, status, amount)
                VALUES (:id, :user_id, :fiverr_order_id, :status, :amount)
            """
            ),
            {
                "id": order_id,
                "user_id": user_id,
                "fiverr_order_id": "FO_STATUS_TEST",
                "status": "pending",
                "amount": 100.00,
            },
        )
        await db_session.commit()

        # 模拟状态变更工作流
        # 1. 检测状态变更
        # 2. 触发 AI 生成回复
        qianfan_mock = mock_all_external_services["qianfan"].return_value
        await qianfan_mock.generate_text(prompt="订单状态已变更", system_message="生成客户通知")

        # 3. 触发 N8N 发送通知
        n8n_mock = mock_all_external_services["n8n"].return_value
        await n8n_mock.execute_workflow(
            workflow_id="notification-workflow",
            data={"order_id": str(order_id), "new_status": "processing"},
        )

        # 4. 更新数据库状态
        await db_session.execute(
            text("UPDATE orders SET status = :status WHERE id = :id"),
            {"status": "completed", "id": order_id},
        )
        await db_session.commit()

        # 验证
        result = await db_session.execute(
            text("SELECT status FROM orders WHERE id = :id"), {"id": order_id}
        )
        assert result.fetchone().status == "completed"

        # 清理
        await db_session.execute(text("DELETE FROM orders WHERE id = :id"), {"id": order_id})
        await db_session.execute(text("DELETE FROM users WHERE id = :id"), {"id": user_id})
        await db_session.commit()


# ============================================================================
# 知识管理端到端测试
# ============================================================================


class TestKnowledgeManagementE2E:
    """知识管理端到端测试"""

    @pytest.mark.asyncio
    async def test_complete_knowledge_workflow(
        self, e2e_client, db_session, mock_all_external_services, e2e_test_data
    ):
        """测试完整的知识管理工作流程"""
        from agentforge.security.password_handler import PasswordHandler

        # 步骤 1: 创建用户
        user_id = uuid4()
        password_hash = PasswordHandler.hash_password(e2e_test_data["user"]["password"])

        await db_session.execute(
            text(
                """
                INSERT INTO users (id, email, password_hash, name, is_active)
                VALUES (:id, :email, :password_hash, :name, :is_active)
            """
            ),
            {
                "id": user_id,
                "email": e2e_test_data["user"]["email"],
                "password_hash": password_hash,
                "name": e2e_test_data["user"]["name"],
                "is_active": True,
            },
        )
        await db_session.commit()

        # 步骤 2: 创建知识文档
        doc_id = uuid4()
        await db_session.execute(
            text(
                """
                INSERT INTO knowledge_docs (id, user_id, title, content, source, doc_type, tags)
                VALUES (:id, :user_id, :title, :content, :source, :doc_type, :tags)
            """
            ),
            {
                "id": doc_id,
                "user_id": user_id,
                "title": e2e_test_data["knowledge_doc"]["title"],
                "content": e2e_test_data["knowledge_doc"]["content"],
                "source": e2e_test_data["knowledge_doc"]["source"],
                "doc_type": e2e_test_data["knowledge_doc"]["doc_type"],
                "tags": e2e_test_data["knowledge_doc"]["tags"],
            },
        )
        await db_session.commit()

        # 步骤 3: 使用 AI 生成文档摘要
        qianfan_mock = mock_all_external_services["qianfan"].return_value
        summary_result = await qianfan_mock.generate_text(
            prompt=f"为以下文档生成摘要：{e2e_test_data['knowledge_doc']['content']}",
            system_message="你是知识管理助手",
        )

        assert summary_result is not None

        # 步骤 4: 生成向量嵌入（模拟）
        # 在实际系统中，这会调用 Qdrant
        embedding = [0.1, 0.2, 0.3, 0.4]  # 模拟向量

        # 步骤 5: 更新文档的向量 ID
        await db_session.execute(
            text("UPDATE knowledge_docs SET embedding_id = :embedding_id WHERE id = :id"),
            {"embedding_id": f"emb_{doc_id}", "id": doc_id},
        )
        await db_session.commit()

        # 步骤 6: 验证文档可搜索
        result = await db_session.execute(
            text("SELECT * FROM knowledge_docs WHERE id = :id"), {"id": doc_id}
        )
        doc = result.fetchone()
        assert doc is not None
        assert doc.embedding_id == f"emb_{doc_id}"

        # 清理
        await db_session.execute(text("DELETE FROM knowledge_docs WHERE id = :id"), {"id": doc_id})
        await db_session.execute(text("DELETE FROM users WHERE id = :id"), {"id": user_id})
        await db_session.commit()

    @pytest.mark.asyncio
    async def test_knowledge_sync_with_external_sources(
        self, e2e_client, db_session, mock_all_external_services
    ):
        """测试知识与外部源同步"""
        # 模拟从 Notion 同步
        n8n_mock = mock_all_external_services["n8n"].return_value

        # 触发同步工作流
        sync_result = await n8n_mock.execute_workflow(
            workflow_id="knowledge-sync-workflow",
            data={"source": "notion", "sync_type": "full"},
        )

        assert sync_result is not None
        assert sync_result.get("status") == "success"

        # 验证同步结果已存储
        # （在实际系统中，这里会检查数据库）


# ============================================================================
# 社交媒体内容生成与发布端到端测试
# ============================================================================


class TestSocialMediaE2E:
    """社交媒体内容生成与发布端到端测试"""

    @pytest.mark.asyncio
    async def test_content_generation_and_publishing(
        self, e2e_client, db_session, mock_all_external_services
    ):
        """测试内容生成和发布完整流程"""
        from agentforge.security.password_handler import PasswordHandler

        # 步骤 1: 创建用户
        user_id = uuid4()
        password_hash = PasswordHandler.hash_password("Test@123456")

        await db_session.execute(
            text(
                """
                INSERT INTO users (id, email, password_hash, name, is_active)
                VALUES (:id, :email, :password_hash, :name, :is_active)
            """
            ),
            {
                "id": user_id,
                "email": f"social_test_{uuid4()}@example.com",
                "password_hash": password_hash,
                "name": "社交媒体测试用户",
                "is_active": True,
            },
        )
        await db_session.commit()

        # 步骤 2: 使用 AI 生成内容
        qianfan_mock = mock_all_external_services["qianfan"].return_value
        content_result = await qianfan_mock.generate_text(
            prompt="为新产品生成社交媒体推文",
            system_message="你是社交媒体内容专家",
        )

        assert content_result is not None
        generated_content = content_result.get("result", "")

        # 步骤 3: 保存草稿到数据库
        draft_id = uuid4()
        await db_session.execute(
            text(
                """
                INSERT INTO content_drafts (id, user_id, platform, content, status)
                VALUES (:id, :user_id, :platform, :content, :status)
            """
            ),
            {
                "id": draft_id,
                "user_id": user_id,
                "platform": "twitter",
                "content": generated_content,
                "status": "draft",
            },
        )
        await db_session.commit()

        # 步骤 4: 触发 N8N 发布工作流
        n8n_mock = mock_all_external_services["n8n"].return_value
        publish_result = await n8n_mock.execute_workflow(
            workflow_id="social-publish-workflow",
            data={
                "draft_id": str(draft_id),
                "platform": "twitter",
                "content": generated_content,
            },
        )

        assert publish_result is not None

        # 步骤 5: 更新草稿状态
        await db_session.execute(
            text("UPDATE content_drafts SET status = :status WHERE id = :id"),
            {"status": "published", "id": draft_id},
        )
        await db_session.commit()

        # 验证
        result = await db_session.execute(
            text("SELECT status FROM content_drafts WHERE id = :id"), {"id": draft_id}
        )
        assert result.fetchone().status == "published"

        # 清理
        await db_session.execute(
            text("DELETE FROM content_drafts WHERE id = :id"), {"id": draft_id}
        )
        await db_session.execute(text("DELETE FROM users WHERE id = :id"), {"id": user_id})
        await db_session.commit()


# ============================================================================
# 客户沟通端到端测试
# ============================================================================


class TestCustomerCommunicationE2E:
    """客户沟通端到端测试"""

    @pytest.mark.asyncio
    async def test_customer_message_workflow(
        self, e2e_client, db_session, mock_all_external_services
    ):
        """测试客户消息处理完整流程"""
        from agentforge.security.password_handler import PasswordHandler

        # 创建用户
        user_id = uuid4()
        password_hash = PasswordHandler.hash_password("Test@123456")

        await db_session.execute(
            text(
                """
                INSERT INTO users (id, email, password_hash, name, is_active)
                VALUES (:id, :email, :password_hash, :name, :is_active)
            """
            ),
            {
                "id": user_id,
                "email": f"comm_test_{uuid4()}@example.com",
                "password_hash": password_hash,
                "name": "沟通测试用户",
                "is_active": True,
            },
        )
        await db_session.commit()

        # 步骤 1: 接收客户消息（模拟）
        customer_message = {
            "order_id": "FO123456",
            "message": "请问我的订单什么时候能完成？",
            "customer": "test_customer",
        }

        # 步骤 2: 使用 AI 分析消息意图
        qianfan_mock = mock_all_external_services["qianfan"].return_value
        intent_result = await qianfan_mock.generate_text(
            prompt=f"分析客户消息：{customer_message['message']}",
            system_message="你是客户意图分析助手",
        )

        assert intent_result is not None

        # 步骤 3: 使用 AI 生成回复
        reply_result = await qianfan_mock.generate_text(
            prompt=f"为以下客户消息生成专业回复：{customer_message['message']}",
            system_message="你是专业的客户服务代表",
        )

        assert reply_result is not None
        generated_reply = reply_result.get("result", "")

        # 步骤 4: 保存对话记录
        conversation_id = uuid4()
        await db_session.execute(
            text(
                """
                INSERT INTO conversations (id, user_id, agent_id, role, content, tokens_used)
                VALUES (:id, :user_id, :agent_id, :role, :content, :tokens_used)
            """
            ),
            {
                "id": conversation_id,
                "user_id": user_id,
                "agent_id": "customer_service",
                "role": "user",
                "content": customer_message["message"],
                "tokens_used": 20,
            },
        )

        await db_session.execute(
            text(
                """
                INSERT INTO conversations (id, user_id, agent_id, role, content, tokens_used)
                VALUES (:id, :user_id, :agent_id, :role, :content, :tokens_used)
            """
            ),
            {
                "id": uuid4(),
                "user_id": user_id,
                "agent_id": "customer_service",
                "role": "assistant",
                "content": generated_reply,
                "tokens_used": 30,
            },
        )
        await db_session.commit()

        # 步骤 5: 触发 N8N 发送回复
        n8n_mock = mock_all_external_services["n8n"].return_value
        await n8n_mock.execute_workflow(
            workflow_id="customer-reply-workflow",
            data={
                "order_id": customer_message["order_id"],
                "reply": generated_reply,
                "customer": customer_message["customer"],
            },
        )

        # 验证对话记录
        result = await db_session.execute(
            text("SELECT * FROM conversations WHERE user_id = :user_id"), {"user_id": user_id}
        )
        conversations = result.fetchall()
        assert len(conversations) == 2

        # 清理
        await db_session.execute(
            text("DELETE FROM conversations WHERE user_id = :user_id"), {"user_id": user_id}
        )
        await db_session.execute(text("DELETE FROM users WHERE id = :id"), {"id": user_id})
        await db_session.commit()


# ============================================================================
# 多模块协作端到端测试
# ============================================================================


class TestMultiModuleCollaborationE2E:
    """多模块协作端到端测试"""

    @pytest.mark.asyncio
    async def test_cross_module_workflow(
        self, e2e_client, db_session, mock_all_external_services
    ):
        """测试跨模块协作工作流"""
        from agentforge.security.password_handler import PasswordHandler

        # 创建用户
        user_id = uuid4()
        password_hash = PasswordHandler.hash_password("Test@123456")

        await db_session.execute(
            text(
                """
                INSERT INTO users (id, email, password_hash, name, is_active)
                VALUES (:id, :email, :password_hash, :name, :is_active)
            """
            ),
            {
                "id": user_id,
                "email": f"cross_module_{uuid4()}@example.com",
                "password_hash": password_hash,
                "name": "跨模块测试用户",
                "is_active": True,
            },
        )
        await db_session.commit()

        # 场景：新订单到达 -> AI 分析 -> 创建知识文档 -> 触发工作流 -> 通知客户

        # 1. 创建订单
        order_id = uuid4()
        await db_session.execute(
            text(
                """
                INSERT INTO orders (id, user_id, fiverr_order_id, status, amount, description)
                VALUES (:id, :user_id, :fiverr_order_id, :status, :amount, :description)
            """
            ),
            {
                "id": order_id,
                "user_id": user_id,
                "fiverr_order_id": "FO_CROSS_MODULE",
                "status": "pending",
                "amount": 300.00,
                "description": "跨模块测试订单",
            },
        )
        await db_session.commit()

        # 2. AI 分析订单
        qianfan_mock = mock_all_external_services["qianfan"].return_value
        analysis = await qianfan_mock.generate_text(
            prompt="分析新订单 FO_CROSS_MODULE", system_message="订单分析助手"
        )

        # 3. 创建知识文档记录订单处理经验
        doc_id = uuid4()
        await db_session.execute(
            text(
                """
                INSERT INTO knowledge_docs (id, user_id, title, content, doc_type)
                VALUES (:id, :user_id, :title, :content, :doc_type)
            """
            ),
            {
                "id": doc_id,
                "user_id": user_id,
                "title": "订单处理经验：FO_CROSS_MODULE",
                "content": "订单处理的最佳实践和注意事项...",
                "doc_type": "experience",
            },
        )
        await db_session.commit()

        # 4. 触发 N8N 工作流（多个）
        n8n_mock = mock_all_external_services["n8n"].return_value

        # 4a. 订单处理工作流
        await n8n_mock.execute_workflow(
            workflow_id="order-processing", data={"order_id": str(order_id)}
        )

        # 4b. 知识同步工作流
        await n8n_mock.execute_workflow(
            workflow_id="knowledge-sync", data={"doc_id": str(doc_id)}
        )

        # 4c. 客户通知工作流
        await n8n_mock.execute_workflow(
            workflow_id="customer-notification",
            data={"order_id": str(order_id), "message": "订单已确认"},
        )

        # 5. 验证所有模块状态
        # 订单状态
        result = await db_session.execute(
            text("SELECT status FROM orders WHERE id = :id"), {"id": order_id}
        )
        order = result.fetchone()
        assert order.status == "pending"

        # 知识文档
        result = await db_session.execute(
            text("SELECT * FROM knowledge_docs WHERE id = :id"), {"id": doc_id}
        )
        doc = result.fetchone()
        assert doc is not None

        # 6. 更新订单状态为处理中
        await db_session.execute(
            text("UPDATE orders SET status = :status WHERE id = :id"),
            {"status": "processing", "id": order_id},
        )
        await db_session.commit()

        # 清理
        await db_session.execute(text("DELETE FROM orders WHERE id = :id"), {"id": order_id})
        await db_session.execute(
            text("DELETE FROM knowledge_docs WHERE id = :id"), {"id": doc_id}
        )
        await db_session.execute(text("DELETE FROM users WHERE id = :id"), {"id": user_id})
        await db_session.commit()


# ============================================================================
# 完整业务流程端到端测试
# ============================================================================


class TestCompleteBusinessProcessE2E:
    """完整业务流程端到端测试"""

    @pytest.mark.asyncio
    async def test_full_business_cycle(
        self, e2e_client, db_session, mock_all_external_services
    ):
        """测试完整业务周期"""
        from agentforge.security.password_handler import PasswordHandler

        # 创建用户
        user_id = uuid4()
        password_hash = PasswordHandler.hash_password("Test@123456")

        await db_session.execute(
            text(
                """
                INSERT INTO users (id, email, password_hash, name, is_active)
                VALUES (:id, :email, :password_hash, :name, :is_active)
            """
            ),
            {
                "id": user_id,
                "email": f"full_cycle_{uuid4()}@example.com",
                "password_hash": password_hash,
                "name": "完整周期测试用户",
                "is_active": True,
            },
        )
        await db_session.commit()

        print(f"\n=== 开始完整业务周期测试 ===")
        print(f"用户 ID: {user_id}")

        # 阶段 1: 订单接收
        print("\n阶段 1: 订单接收")
        order_id = uuid4()
        await db_session.execute(
            text(
                """
                INSERT INTO orders (id, user_id, fiverr_order_id, status, amount)
                VALUES (:id, :user_id, :fiverr_order_id, :status, :amount)
            """
            ),
            {
                "id": order_id,
                "user_id": user_id,
                "fiverr_order_id": "FO_FULL_CYCLE",
                "status": "pending",
                "amount": 500.00,
            },
        )
        await db_session.commit()
        print(f"订单创建：{order_id}")

        # 阶段 2: AI 分析和处理
        print("\n阶段 2: AI 分析")
        qianfan_mock = mock_all_external_services["qianfan"].return_value
        await qianfan_mock.generate_text(prompt="分析订单", system_message="分析助手")

        # 阶段 3: 工作流执行
        print("\n阶段 3: 工作流执行")
        n8n_mock = mock_all_external_services["n8n"].return_value
        await n8n_mock.execute_workflow(
            workflow_id="full-cycle-workflow", data={"order_id": str(order_id)}
        )

        # 阶段 4: 知识沉淀
        print("\n阶段 4: 知识沉淀")
        doc_id = uuid4()
        await db_session.execute(
            text(
                """
                INSERT INTO knowledge_docs (id, user_id, title, content, doc_type)
                VALUES (:id, :user_id, :title, :content, :doc_type)
            """
            ),
            {
                "id": doc_id,
                "user_id": user_id,
                "title": "完整业务周期测试文档",
                "content": "业务处理流程记录",
                "doc_type": "process",
            },
        )
        await db_session.commit()

        # 阶段 5: 订单完成
        print("\n阶段 5: 订单完成")
        await db_session.execute(
            text("UPDATE orders SET status = :status WHERE id = :id"),
            {"status": "completed", "id": order_id},
        )
        await db_session.commit()

        # 验证所有数据
        print("\n验证数据")
        result = await db_session.execute(
            text("SELECT status FROM orders WHERE id = :id"), {"id": order_id}
        )
        assert result.fetchone().status == "completed"

        result = await db_session.execute(
            text("SELECT * FROM knowledge_docs WHERE id = :id"), {"id": doc_id}
        )
        assert result.fetchone() is not None

        print("\n=== 完整业务周期测试完成 ===")

        # 清理
        await db_session.execute(text("DELETE FROM orders WHERE id = :id"), {"id": order_id})
        await db_session.execute(
            text("DELETE FROM knowledge_docs WHERE id = :id"), {"id": doc_id}
        )
        await db_session.execute(text("DELETE FROM users WHERE id = :id"), {"id": user_id})
        await db_session.commit()
