"""
工作流集成测试
测试 N8N 工作流引擎与业务引擎的集成

测试场景：
1. N8N 客户端基础操作
2. 工作流定义和部署
3. 工作流执行和监控
4. Fiverr 订单监控工作流
5. 知识同步工作流
6. 社交媒体发布工作流
7. 错误处理和重试机制
"""
import pytest
import asyncio
from typing import Dict, Any, List
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from integrations.n8n.n8n_client import (
    N8NClient,
    WorkflowDefinition,
    WorkflowExecution,
)
from agentforge.config import settings


# ============================================================================
# 测试夹具
# ============================================================================


@pytest.fixture
def n8n_client():
    """创建 N8N 客户端实例"""
    client = N8NClient(
        host="localhost",
        port=5678,
        username="admin",
        password="test_password",
    )
    yield client


@pytest.fixture
def mock_httpx_client():
    """模拟 httpx 客户端"""
    with patch("httpx.AsyncClient") as mock_client:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": []}

        mock_client_instance = AsyncMock()
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        mock_client_instance.patch = AsyncMock(return_value=mock_response)
        mock_client_instance.delete = AsyncMock(return_value=mock_response)
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=None)

        mock_client.return_value = mock_client_instance
        yield mock_client


@pytest.fixture
def sample_workflow_definition():
    """示例工作流定义"""
    return WorkflowDefinition(
        name="测试工作流",
        description="用于集成测试的工作流",
        nodes=[
            {
                "name": "Start",
                "type": "n8n-nodes-base.manualTrigger",
                "position": [250, 300],
                "parameters": {},
            }
        ],
        connections={},
        active=False,
    )


@pytest.fixture
def fiverr_order_workflow():
    """Fiverr 订单监控工作流定义"""
    return WorkflowDefinition(
        name="Fiverr 订单监控",
        description="自动监控和处理 Fiverr 订单",
        nodes=[
            {
                "name": "定时触发器",
                "type": "n8n-nodes-base.scheduleTrigger",
                "position": [250, 300],
                "parameters": {"rule": {"interval": [{"field": "hours", "hoursInterval": 1}]}},
            },
            {
                "name": "获取订单",
                "type": "n8n-nodes-base.httpRequest",
                "position": [450, 300],
                "parameters": {
                    "url": "http://agentforge-core:8080/api/fiverr/orders",
                    "method": "GET",
                },
            },
            {
                "name": "AI 处理",
                "type": "n8n-nodes-base.httpRequest",
                "position": [650, 300],
                "parameters": {
                    "url": "http://agentforge-core:8080/api/chat",
                    "method": "POST",
                    "jsonParameters": True,
                    "bodyParametersJson": '={"message": "处理新订单"}',
                },
            },
        ],
        connections={
            "定时触发器": {"main": [[{"node": "获取订单", "type": "main", "index": 0}]]},
            "获取订单": {"main": [[{"node": "AI 处理", "type": "main", "index": 0}]]},
        },
    )


# ============================================================================
# N8N 客户端基础测试
# ============================================================================


class TestN8NClientBasics:
    """N8N 客户端基础功能测试"""

    @pytest.mark.asyncio
    async def test_client_initialization(self, n8n_client):
        """测试客户端初始化"""
        assert n8n_client.host == "localhost"
        assert n8n_client.port == 5678
        assert n8n_client.base_url == "http://localhost:5678"
        assert n8n_client.username == "admin"
        assert n8n_client.password == "test_password"

    @pytest.mark.asyncio
    async def test_client_initialize_success(self, n8n_client, mock_httpx_client):
        """测试客户端连接初始化成功"""
        # 模拟健康检查成功
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_httpx_client.return_value.get.return_value = mock_response

        result = await n8n_client.initialize()

        assert result is True
        assert n8n_client._initialized is True

    @pytest.mark.asyncio
    async def test_client_initialize_failure(self, n8n_client, mock_httpx_client):
        """测试客户端连接初始化失败"""
        # 模拟连接失败
        mock_httpx_client.return_value.get.side_effect = Exception("连接失败")

        result = await n8n_client.initialize()

        assert result is False
        assert n8n_client._initialized is False


# ============================================================================
# 工作流管理测试
# ============================================================================


class TestWorkflowManagement:
    """工作流管理测试"""

    @pytest.mark.asyncio
    async def test_list_workflows(self, n8n_client, mock_httpx_client):
        """测试获取工作流列表"""
        # 模拟返回工作流列表
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"id": "1", "name": "工作流 1", "active": True},
                {"id": "2", "name": "工作流 2", "active": False},
            ]
        }
        mock_httpx_client.return_value.get.return_value = mock_response

        workflows = await n8n_client.list_workflows()

        assert len(workflows) == 2
        assert workflows[0]["name"] == "工作流 1"
        assert workflows[1]["active"] is False

    @pytest.mark.asyncio
    async def test_get_workflow(self, n8n_client, mock_httpx_client):
        """测试获取单个工作流"""
        # 模拟返回工作流详情
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "id": "workflow-123",
                "name": "测试工作流",
                "description": "测试描述",
                "active": True,
            }
        }
        mock_httpx_client.return_value.get.return_value = mock_response

        workflow = await n8n_client.get_workflow("workflow-123")

        assert workflow is not None
        assert workflow["id"] == "workflow-123"
        assert workflow["name"] == "测试工作流"

    @pytest.mark.asyncio
    async def test_create_workflow(self, n8n_client, mock_httpx_client, sample_workflow_definition):
        """测试创建工作流"""
        # 模拟创建成功
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": {"id": "new-workflow-123"}}
        mock_httpx_client.return_value.post.return_value = mock_response

        workflow_id = await n8n_client.create_workflow(sample_workflow_definition)

        assert workflow_id == "new-workflow-123"
        mock_httpx_client.return_value.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_activate_workflow(self, n8n_client, mock_httpx_client):
        """测试激活工作流"""
        # 模拟激活成功
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_httpx_client.return_value.patch.return_value = mock_response

        result = await n8n_client.activate_workflow("workflow-123")

        assert result is True
        mock_httpx_client.return_value.patch.assert_called_once()

    @pytest.mark.asyncio
    async def test_deactivate_workflow(self, n8n_client, mock_httpx_client):
        """测试停用工作流"""
        # 模拟停用成功
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_httpx_client.return_value.patch.return_value = mock_response

        result = await n8n_client.deactivate_workflow("workflow-123")

        assert result is True

    @pytest.mark.asyncio
    async def test_delete_workflow(self, n8n_client, mock_httpx_client):
        """测试删除工作流"""
        # 模拟删除成功
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_httpx_client.return_value.delete.return_value = mock_response

        result = await n8n_client.delete_workflow("workflow-123")

        assert result is True


# ============================================================================
# 工作流执行测试
# ============================================================================


class TestWorkflowExecution:
    """工作流执行测试"""

    @pytest.mark.asyncio
    async def test_execute_workflow(self, n8n_client, mock_httpx_client):
        """测试执行工作流"""
        # 模拟执行成功
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"executionId": "exec-123"}
        mock_httpx_client.return_value.post.return_value = mock_response

        execution = await n8n_client.execute_workflow(
            workflow_id="workflow-123", data={"test_key": "test_value"}
        )

        assert execution is not None
        assert execution.execution_id == "exec-123"
        assert execution.workflow_id == "workflow-123"
        assert execution.status == "running"

    @pytest.mark.asyncio
    async def test_execute_workflow_with_empty_data(self, n8n_client, mock_httpx_client):
        """测试执行工作流（无数据）"""
        # 模拟执行成功
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"executionId": "exec-456"}
        mock_httpx_client.return_value.post.return_value = mock_response

        execution = await n8n_client.execute_workflow(workflow_id="workflow-123")

        assert execution is not None
        assert execution.execution_id == "exec-456"

    @pytest.mark.asyncio
    async def test_get_execution_details(self, n8n_client, mock_httpx_client):
        """测试获取执行详情"""
        # 模拟返回执行详情
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "id": "exec-123",
                "status": "success",
                "startedAt": "2024-01-01T00:00:00.000Z",
                "finishedAt": "2024-01-01T00:01:00.000Z",
            }
        }
        mock_httpx_client.return_value.get.return_value = mock_response

        execution = await n8n_client.get_execution("exec-123")

        assert execution is not None
        assert execution["id"] == "exec-123"
        assert execution["status"] == "success"


# ============================================================================
# 业务场景工作流测试
# ============================================================================


class TestBusinessWorkflows:
    """业务场景工作流测试"""

    @pytest.mark.asyncio
    async def test_fiverr_order_workflow_creation(
        self, n8n_client, mock_httpx_client, fiverr_order_workflow
    ):
        """测试创建 Fiverr 订单监控工作流"""
        # 模拟创建成功
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": {"id": "fiverr-workflow-123"}}
        mock_httpx_client.return_value.post.return_value = mock_response

        workflow_id = await n8n_client.create_workflow(fiverr_order_workflow)

        assert workflow_id == "fiverr-workflow-123"

        # 验证工作流定义
        assert fiverr_order_workflow.name == "Fiverr 订单监控"
        assert len(fiverr_order_workflow.nodes) == 3
        assert "定时触发器" in fiverr_order_workflow.connections

    @pytest.mark.asyncio
    async def test_knowledge_sync_workflow(self, n8n_client, mock_httpx_client):
        """测试知识同步工作流"""
        workflow = n8n_client.create_knowledge_sync_workflow()

        # 验证工作流定义
        assert workflow.name == "Knowledge Sync"
        assert len(workflow.nodes) == 2
        assert workflow.nodes[0]["type"] == "n8n-nodes-base.scheduleTrigger"

        # 模拟创建
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": {"id": "knowledge-sync-123"}}
        mock_httpx_client.return_value.post.return_value = mock_response

        workflow_id = await n8n_client.create_workflow(workflow)

        assert workflow_id == "knowledge-sync-123"

    @pytest.mark.asyncio
    async def test_social_media_workflow(self, n8n_client, mock_httpx_client):
        """测试社交媒体发布工作流"""
        workflow = n8n_client.create_social_media_workflow()

        # 验证工作流定义
        assert workflow.name == "Social Media Publisher"
        assert len(workflow.nodes) == 2
        assert workflow.nodes[0]["type"] == "n8n-nodes-base.webhook"

        # 模拟创建
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": {"id": "social-media-123"}}
        mock_httpx_client.return_value.post.return_value = mock_response

        workflow_id = await n8n_client.create_workflow(workflow)

        assert workflow_id == "social-media-123"


# ============================================================================
# 工作流与业务引擎集成测试
# ============================================================================


class TestWorkflowBusinessIntegration:
    """工作流与业务引擎集成测试"""

    @pytest.mark.asyncio
    async def test_workflow_triggers_fiverr_processing(
        self, n8n_client, mock_httpx_client, mock_external_services
    ):
        """测试工作流触发 Fiverr 订单处理"""
        # 模拟工作流执行
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"executionId": "fiverr-exec-123"}
        mock_httpx_client.return_value.post.return_value = mock_response

        # 执行工作流
        execution = await n8n_client.execute_workflow(
            workflow_id="fiverr-workflow",
            data={"order_id": "FO123456", "action": "process_new_order"},
        )

        assert execution is not None
        assert execution.execution_id == "fiverr-exec-123"

    @pytest.mark.asyncio
    async def test_workflow_with_ai_model_integration(
        self, n8n_client, mock_httpx_client, mock_external_services
    ):
        """测试工作流与 AI 模型集成"""
        # 模拟工作流调用 AI 服务
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "executionId": "ai-exec-123",
            "result": {"message": "AI 处理完成"},
        }
        mock_httpx_client.return_value.post.return_value = mock_response

        execution = await n8n_client.execute_workflow(
            workflow_id="ai-workflow",
            data={"prompt": "分析订单数据", "model": "glm-5"},
        )

        assert execution is not None

    @pytest.mark.asyncio
    async def test_workflow_error_handling(self, n8n_client, mock_httpx_client):
        """测试工作流错误处理"""
        # 模拟执行失败
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.json.return_value = {"error": "工作流执行失败"}
        mock_httpx_client.return_value.post.return_value = mock_response

        execution = await n8n_client.execute_workflow(workflow_id="invalid-workflow")

        # 失败时返回 None
        assert execution is None


# ============================================================================
# 工作流定时和调度测试
# ============================================================================


class TestWorkflowScheduling:
    """工作流定时和调度测试"""

    @pytest.mark.asyncio
    async def test_schedule_trigger_workflow(self, n8n_client, mock_httpx_client):
        """测试定时触发工作流"""
        # 创建工作流（带定时触发器）
        workflow = n8n_client.create_fiverr_order_workflow()

        # 验证触发器配置
        trigger_node = workflow.nodes[0]
        assert trigger_node["type"] == "n8n-nodes-base.scheduleTrigger"
        assert "interval" in trigger_node["parameters"]["rule"]

        # 模拟创建和激活
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": {"id": "scheduled-workflow-123"}}
        mock_httpx_client.return_value.post.return_value = mock_response

        workflow_id = await n8n_client.create_workflow(workflow)

        # 激活工作流
        mock_httpx_client.return_value.patch.return_value = MagicMock(status_code=200)
        await n8n_client.activate_workflow(workflow_id)

        assert workflow_id == "scheduled-workflow-123"

    @pytest.mark.asyncio
    async def test_webhook_trigger_workflow(self, n8n_client, mock_httpx_client):
        """测试 Webhook 触发工作流"""
        # 创建 webhook 触发的工作流
        workflow = n8n_client.create_social_media_workflow()

        # 验证 webhook 配置
        webhook_node = workflow.nodes[0]
        assert webhook_node["type"] == "n8n-nodes-base.webhook"
        assert webhook_node["parameters"]["httpMethod"] == "POST"
        assert webhook_node["parameters"]["path"] == "social-publish"


# ============================================================================
# 工作流数据流转测试
# ============================================================================


class TestWorkflowDataFlow:
    """工作流数据流转测试"""

    @pytest.mark.asyncio
    async def test_workflow_data_passing(self, n8n_client, mock_httpx_client):
        """测试工作流数据传递"""
        # 模拟工作流执行并传递数据
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "executionId": "dataflow-exec-123",
            "data": {"processed": True, "result": "数据处理成功"},
        }
        mock_httpx_client.return_value.post.return_value = mock_response

        input_data = {
            "order_id": "FO123",
            "customer": "test_customer",
            "amount": 150.00,
            "items": ["服务 A", "服务 B"],
        }

        execution = await n8n_client.execute_workflow(
            workflow_id="dataflow-workflow", data=input_data
        )

        assert execution is not None
        assert execution.execution_id == "dataflow-exec-123"

    @pytest.mark.asyncio
    async def test_workflow_chained_execution(self, n8n_client, mock_httpx_client):
        """测试工作流链式执行"""
        # 模拟多个工作流依次执行
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"executionId": "chain-exec-1"}
        mock_httpx_client.return_value.post.return_value = mock_response

        # 执行第一个工作流
        execution1 = await n8n_client.execute_workflow(
            workflow_id="workflow-1", data={"step": 1}
        )

        # 模拟第二个执行
        mock_response.json.return_value = {"executionId": "chain-exec-2"}
        execution2 = await n8n_client.execute_workflow(
            workflow_id="workflow-2", data={"step": 2, "previous_result": "chain-exec-1"}
        )

        assert execution1 is not None
        assert execution2 is not None
        assert execution1.execution_id == "chain-exec-1"
        assert execution2.execution_id == "chain-exec-2"


# ============================================================================
# 工作流性能测试
# ============================================================================


class TestWorkflowPerformance:
    """工作流性能测试"""

    @pytest.mark.asyncio
    async def test_concurrent_workflow_executions(self, n8n_client, mock_httpx_client):
        """测试并发工作流执行"""
        # 模拟并发执行
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"executionId": "concurrent-exec"}
        mock_httpx_client.return_value.post.return_value = mock_response

        # 并发执行 5 个工作流
        tasks = [
            n8n_client.execute_workflow(workflow_id=f"workflow-{i}", data={"index": i})
            for i in range(5)
        ]

        results = await asyncio.gather(*tasks)

        assert len(results) == 5
        assert all(result is not None for result in results)
        assert all(result.execution_id == "concurrent-exec" for result in results)

    @pytest.mark.asyncio
    async def test_workflow_execution_timeout(self, n8n_client, mock_httpx_client):
        """测试工作流执行超时"""
        import asyncio

        # 模拟超时
        async def slow_response(*args, **kwargs):
            await asyncio.sleep(0.1)  # 模拟延迟
            raise asyncio.TimeoutError("请求超时")

        mock_httpx_client.return_value.post.side_effect = slow_response

        # 执行工作流（应该超时）
        with pytest.raises(asyncio.TimeoutError):
            await n8n_client.execute_workflow(workflow_id="slow-workflow", data={})
