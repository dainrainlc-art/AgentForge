"""
LLM 模块单元测试

测试 AgentForge LLM 相关功能，包括：
- QianfanClient: 百度千帆客户端
- ModelRouter: 多模型路由器
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

from agentforge.llm.qianfan_client import QianfanClient
from agentforge.llm.model_router import (
    ModelRouter,
    ModelType,
    ModelConfig,
    AVAILABLE_MODELS,
    model_router
)


@pytest.fixture
def mock_httpx_client():
    """Mock httpx AsyncClient"""
    with patch("agentforge.llm.qianfan_client.httpx.AsyncClient") as mock_client:
        client_instance = MagicMock()
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "Test response from API"
                    }
                }
            ]
        }
        client_instance.post = AsyncMock(return_value=mock_response)
        client_instance.__aenter__ = AsyncMock(return_value=client_instance)
        client_instance.__aexit__ = AsyncMock(return_value=None)
        
        mock_client.return_value = client_instance
        yield mock_client


@pytest.fixture
def qianfan_config():
    """Qianfan 测试配置"""
    return {
        "api_key": "test_api_key_12345",
        "base_url": "https://qianfan.baidubce.com/v2/coding",
        "default_model": "glm-5"
    }


class TestQianfanClient:
    """QianfanClient 测试"""
    
    @pytest.mark.asyncio
    async def test_client_initialization(self, qianfan_config):
        """测试客户端初始化"""
        client = QianfanClient(
            api_key=qianfan_config["api_key"],
            base_url=qianfan_config["base_url"],
            default_model=qianfan_config["default_model"]
        )
        
        assert client.api_key == "test_api_key_12345"
        assert client.base_url == "https://qianfan.baidubce.com/v2/coding"
        assert client.default_model == "glm-5"
    
    @pytest.mark.asyncio
    async def test_client_default_initialization(self, qianfan_config):
        """测试客户端默认初始化（使用配置）"""
        with patch("agentforge.llm.qianfan_client.settings") as mock_settings:
            mock_settings.qianfan_api_key = "configured_api_key"
            mock_settings.qianfan_base_url = "https://configured.url"
            mock_settings.qianfan_default_model = "kimi-k2.5"
            
            client = QianfanClient()
            
            assert client.api_key == "configured_api_key"
    
    @pytest.mark.asyncio
    async def test_chat_success(
        self,
        qianfan_config,
        mock_httpx_client
    ):
        """测试聊天成功"""
        client = QianfanClient(**qianfan_config)
        
        response = await client.chat(
            message="Hello, how are you?",
            model="glm-5",
            temperature=0.7,
            max_tokens=1000
        )
        
        assert response == "Test response from API"
        mock_httpx_client.return_value.post.assert_called_once()
        
        call_args = mock_httpx_client.return_value.post.call_args
        assert call_args[1]["json"]["model"] == "glm-5"
        assert call_args[1]["json"]["temperature"] == 0.7
        assert call_args[1]["json"]["max_tokens"] == 1000
    
    @pytest.mark.asyncio
    async def test_chat_with_context_and_history(
        self,
        qianfan_config,
        mock_httpx_client
    ):
        """测试聊天（带上下文和历史）"""
        client = QianfanClient(**qianfan_config)
        
        context = {"user_id": "123", "session": "test"}
        memories = [
            {"content": "Memory 1", "type": "conversation"},
            {"content": "Memory 2", "type": "learning"}
        ]
        history = [
            {"role": "user", "content": "Previous message 1"},
            {"role": "assistant", "content": "Previous response 1"},
            {"role": "user", "content": "Previous message 2"}
        ]
        
        response = await client.chat(
            message="Current message",
            context=context,
            memories=memories,
            history=history
        )
        
        assert response == "Test response from API"
        
        call_args = mock_httpx_client.return_value.post.call_args[1]["json"]
        messages = call_args["messages"]
        
        assert len(messages) >= 4
        assert messages[0]["role"] == "system"
        assert "Memory 1" in messages[0]["content"]
    
    @pytest.mark.asyncio
    async def test_chat_with_empty_memories(
        self,
        qianfan_config,
        mock_httpx_client
    ):
        """测试聊天（空记忆）"""
        client = QianfanClient(**qianfan_config)
        
        response = await client.chat(
            message="Test message",
            memories=[]
        )
        
        assert response == "Test response from API"
        
        call_args = mock_httpx_client.return_value.post.call_args[1]["json"]
        messages = call_args["messages"]
        
        system_messages = [m for m in messages if m["role"] == "system"]
        assert len(system_messages) <= 1
    
    @pytest.mark.asyncio
    async def test_chat_with_api_error(
        self,
        qianfan_config,
        mock_httpx_client
    ):
        """测试聊天（API 错误）"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "error": {
                "message": "Invalid API key",
                "code": "AUTH_ERROR"
            }
        }
        mock_httpx_client.return_value.post.return_value = mock_response
        
        client = QianfanClient(**qianfan_config)
        
        response = await client.chat(message="Test")
        
        assert "Error" in response
        assert "Invalid API key" in response
    
    @pytest.mark.asyncio
    async def test_chat_with_no_api_key(self, qianfan_config):
        """测试聊天（无 API 密钥）"""
        with patch("agentforge.llm.qianfan_client.settings") as mock_settings:
            mock_settings.qianfan_api_key = None
            client = QianfanClient(api_key=None)
            
            response = await client.chat(message="Test")
            
            assert "Error" in response
    
    @pytest.mark.asyncio
    async def test_chat_with_exception(
        self,
        qianfan_config,
        mock_httpx_client
    ):
        """测试聊天（网络异常）"""
        mock_httpx_client.return_value.post.side_effect = Exception(
            "Connection error"
        )
        
        client = QianfanClient(**qianfan_config)
        
        response = await client.chat(message="Test")
        
        assert "Error" in response
        assert "Connection error" in response
    
    @pytest.mark.asyncio
    async def test_chat_stream_success(
        self,
        qianfan_config,
        mock_httpx_client
    ):
        """测试流式聊天成功"""
        class MockStreamResponse:
            async def aiter_lines(self):
                yield 'data: {"choices":[{"delta":{"content":"Hello"}}]}'
                yield 'data: {"choices":[{"delta":{"content":" World"}}]}'
                yield 'data: [DONE]'
        
        mock_context_manager = MagicMock()
        mock_context_manager.__aenter__ = AsyncMock(return_value=MockStreamResponse())
        mock_context_manager.__aexit__ = AsyncMock(return_value=None)
        
        mock_httpx_client.return_value.stream.return_value = mock_context_manager
        
        client = QianfanClient(**qianfan_config)
        
        chunks = []
        async for chunk in client.chat_stream(message="Test"):
            chunks.append(chunk)
        
        assert len(chunks) == 2
        assert chunks[0] == "Hello"
        assert chunks[1] == " World"
    
    @pytest.mark.asyncio
    async def test_chat_stream_no_api_key(self, qianfan_config):
        """测试流式聊天（无 API 密钥）"""
        with patch("agentforge.llm.qianfan_client.settings") as mock_settings:
            mock_settings.qianfan_api_key = None
            client = QianfanClient(api_key=None)
            
            chunks = []
            async for chunk in client.chat_stream(message="Test"):
                chunks.append(chunk)
            
            assert len(chunks) == 1
            assert "Error" in chunks[0]
    
    @pytest.mark.asyncio
    async def test_chat_stream_with_exception(
        self,
        qianfan_config,
        mock_httpx_client
    ):
        """测试流式聊天（异常）"""
        mock_httpx_client.return_value.stream.side_effect = Exception(
            "Stream error"
        )
        
        client = QianfanClient(**qianfan_config)
        
        chunks = []
        async for chunk in client.chat_stream(message="Test"):
            chunks.append(chunk)
        
        assert len(chunks) == 1
        assert "Stream error" in chunks[0]
    
    @pytest.mark.asyncio
    async def test_route_to_model(self, qianfan_config):
        """测试模型路由"""
        client = QianfanClient(**qianfan_config)
        
        assert client.route_to_model("code") == "deepseek-v3.2"
        assert client.route_to_model("long_context") == "kimi-k2.5"
        assert client.route_to_model("creative") == "minimax-m2.5"
        assert client.route_to_model("analysis") == "kimi-k2.5"
        assert client.route_to_model("unknown") == "glm-5"
    
    @pytest.mark.asyncio
    async def test_health_check_success(
        self,
        qianfan_config,
        mock_httpx_client
    ):
        """测试健康检查成功"""
        client = QianfanClient(**qianfan_config)
        
        result = await client.health_check()
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_health_check_failure(
        self,
        qianfan_config,
        mock_httpx_client
    ):
        """测试健康检查失败"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "error": {"message": "API error"}
        }
        mock_httpx_client.return_value.post.return_value = mock_response
        
        client = QianfanClient(**qianfan_config)
        
        result = await client.health_check()
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_health_check_no_api_key(self, qianfan_config):
        """测试健康检查（无 API 密钥）"""
        with patch("agentforge.llm.qianfan_client.settings") as mock_settings:
            mock_settings.qianfan_api_key = None
            client = QianfanClient(api_key=None)
            
            result = await client.health_check()
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_list_available_models(self, qianfan_config):
        """测试列出可用模型"""
        client = QianfanClient(**qianfan_config)
        
        models = client.list_available_models()
        
        assert len(models) == 4
        assert "glm-5" in models
        assert "kimi-k2.5" in models
        assert "deepseek-v3.2" in models
        assert "minimax-m2.5" in models


class TestModelRouter:
    """ModelRouter 测试"""
    
    @pytest.fixture
    def router(self):
        """创建 ModelRouter 实例"""
        return ModelRouter(api_key="test_key")
    
    @pytest.mark.asyncio
    async def test_router_initialization(self, router):
        """测试路由器初始化"""
        assert router.api_key == "test_key"
        assert "glm-5" in router._model_usage
        assert "kimi-k2.5" in router._model_usage
        assert len(router._model_errors) == len(AVAILABLE_MODELS)
    
    @pytest.mark.asyncio
    async def test_select_model_default(self, router):
        """测试选择默认模型"""
        selected = router.select_model(task_type="default")
        
        assert selected == "glm-5"
    
    @pytest.mark.asyncio
    async def test_select_model_by_type(self, router):
        """测试按类型选择模型"""
        assert router.select_model(task_type="code") == "deepseek-v3.2"
        assert router.select_model(task_type="long_context") == "kimi-k2.5"
        assert router.select_model(task_type="creative") == "minimax-m2.5"
    
    @pytest.mark.asyncio
    async def test_select_model_with_preference(self, router):
        """测试按偏好选择模型"""
        selected = router.select_model(
            task_type="default",
            prefer_model="kimi-k2.5"
        )
        
        assert selected == "kimi-k2.5"
    
    @pytest.mark.asyncio
    async def test_select_model_unavailable_preference(self, router):
        """测试偏好模型不可用"""
        router._quota_exceeded.add("kimi-k2.5")
        
        selected = router.select_model(
            task_type="default",
            prefer_model="kimi-k2.5"
        )
        
        assert selected != "kimi-k2.5"
    
    @pytest.mark.asyncio
    async def test_select_model_fallback(self, router):
        """测试模型回退"""
        for model_id in AVAILABLE_MODELS:
            router._quota_exceeded.add(model_id)
        
        selected = router.select_model(task_type="code")
        
        assert selected == "glm-5"
    
    @pytest.mark.asyncio
    async def test_is_model_available(self, router):
        """测试模型可用性检查"""
        assert router._is_model_available("glm-5") is True
        
        router._quota_exceeded.add("glm-5")
        assert router._is_model_available("glm-5") is False
        
        router._quota_exceeded.remove("glm-5")
        assert router._is_model_available("glm-5") is True
    
    @pytest.mark.asyncio
    async def test_is_model_not_available_quota(self, router):
        """测试模型不可用（配额耗尽）"""
        config = AVAILABLE_MODELS["glm-5"]
        router._model_usage["glm-5"] = config.daily_quota + 1
        
        assert router._is_model_available("glm-5") is False
    
    @pytest.mark.asyncio
    async def test_is_model_not_available_errors(self, router):
        """测试模型不可用（错误过多）"""
        now = datetime.now()
        router._model_errors["glm-5"] = [
            now - timedelta(seconds=60),
            now - timedelta(seconds=120),
            now - timedelta(seconds=180),
            now - timedelta(seconds=240)
        ]
        
        assert router._is_model_available("glm-5") is False
    
    @pytest.mark.asyncio
    async def test_chat_with_failover_success(
        self,
        router,
        mock_httpx_client
    ):
        """测试聊天故障转移成功"""
        with patch.object(router, "_execute_chat", new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = "Success response"
            
            response = await router.chat_with_failover(
                message="Test message",
                task_type="default"
            )
            
            assert response == "Success response"
            mock_execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_chat_with_failover_retry(
        self,
        router,
        mock_httpx_client
    ):
        """测试聊天故障转移重试"""
        async def mock_execute(*args, **kwargs):
            return "Success response"
        
        with patch.object(router, "_execute_chat", new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = "Success response"
            
            response = await router.chat_with_failover(
                message="Test message",
                task_type="default"
            )
            
            assert response == "Success response"
            mock_execute.assert_called()
    
    @pytest.mark.asyncio
    async def test_chat_with_failover_all_fail(
        self,
        router,
        mock_httpx_client
    ):
        """测试聊天故障转移全部失败"""
        with patch.object(router, "_execute_chat", new_callable=AsyncMock) as mock_execute:
            mock_execute.side_effect = Exception("All models failed")
            
            with pytest.raises(Exception) as exc_info:
                await router.chat_with_failover(message="Test")
            
            assert "All models failed" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_execute_chat_no_api_key(self, router):
        """测试执行聊天（无 API 密钥）"""
        router.api_key = None
        
        with pytest.raises(ValueError, match="API key not configured"):
            await router._execute_chat(
                model_id="glm-5",
                message="Test"
            )
    
    @pytest.mark.asyncio
    async def test_execute_chat_success(
        self,
        router,
        mock_httpx_client
    ):
        """测试执行聊天成功"""
        response = await router._execute_chat(
            model_id="glm-5",
            message="Test message",
            temperature=0.7,
            max_tokens=1000
        )
        
        assert response == "Test response from API"
    
    @pytest.mark.asyncio
    async def test_execute_chat_with_context(
        self,
        router,
        mock_httpx_client
    ):
        """测试执行聊天（带上下文）"""
        context = {"user_id": "123"}
        memories = [{"content": "Test memory"}]
        history = [
            {"role": "user", "content": "Previous"},
            {"role": "assistant", "content": "Response"}
        ]
        
        response = await router._execute_chat(
            model_id="glm-5",
            message="Current",
            context=context,
            memories=memories,
            history=history
        )
        
        assert response == "Test response from API"
        
        call_args = mock_httpx_client.return_value.post.call_args[1]["json"]
        messages = call_args["messages"]
        
        assert len(messages) >= 3
    
    @pytest.mark.asyncio
    async def test_execute_chat_with_api_error(
        self,
        router,
        mock_httpx_client
    ):
        """测试执行聊天（API 错误）"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "error": {"message": "API error"}
        }
        mock_httpx_client.return_value.post.return_value = mock_response
        
        with pytest.raises(Exception, match="API error"):
            await router._execute_chat(
                model_id="glm-5",
                message="Test"
            )
    
    @pytest.mark.asyncio
    async def test_execute_chat_with_empty_choices(
        self,
        router,
        mock_httpx_client
    ):
        """测试执行聊天（空选择）"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": []
        }
        mock_httpx_client.return_value.post.return_value = mock_response
        
        response = await router._execute_chat(
            model_id="glm-5",
            message="Test"
        )
        
        assert response == ""
    
    @pytest.mark.asyncio
    async def test_get_usage_stats(self, router):
        """测试获取使用统计"""
        router._model_usage["glm-5"] = 10
        router._model_usage["kimi-k2.5"] = 5
        router._quota_exceeded.add("deepseek-v3.2")
        
        stats = router.get_usage_stats()
        
        assert "usage" in stats
        assert "quota_exceeded" in stats
        assert "model_errors" in stats
        assert stats["usage"]["glm-5"] == 10
    
    @pytest.mark.asyncio
    async def test_reset_daily_stats(self, router):
        """测试重置每日统计"""
        router._model_usage["glm-5"] = 100
        router._quota_exceeded.add("kimi-k2.5")
        
        router.reset_daily_stats()
        
        assert router._model_usage["glm-5"] == 0
        assert len(router._quota_exceeded) == 0


class TestModelConfig:
    """ModelConfig 测试"""
    
    def test_model_config_creation(self):
        """测试模型配置创建"""
        config = ModelConfig(
            model_id="test-model",
            model_type=ModelType.DEFAULT,
            max_tokens=2048,
            temperature=0.5,
            priority=1,
            enabled=True,
            daily_quota=1000
        )
        
        assert config.model_id == "test-model"
        assert config.model_type == ModelType.DEFAULT
        assert config.max_tokens == 2048
        assert config.temperature == 0.5
        assert config.priority == 1
        assert config.enabled is True
        assert config.daily_quota == 1000
        assert config.used_today == 0
    
    def test_model_config_defaults(self):
        """测试模型配置默认值"""
        config = ModelConfig(
            model_id="test",
            model_type=ModelType.CODE
        )
        
        assert config.max_tokens == 4096
        assert config.temperature == 0.7
        assert config.priority == 1
        assert config.enabled is True
        assert config.daily_quota is None


class TestModelType:
    """ModelType 枚举测试"""
    
    def test_model_type_values(self):
        """测试模型类型值"""
        assert ModelType.DEFAULT.value == "default"
        assert ModelType.CODE.value == "code"
        assert ModelType.LONG_CONTEXT.value == "long_context"
        assert ModelType.CREATIVE.value == "creative"
        assert ModelType.ANALYSIS.value == "analysis"


class TestGlobalModelRouter:
    """全局 model_router 实例测试"""
    
    def test_global_router_exists(self):
        """测试全局路由器存在"""
        assert model_router is not None
        assert isinstance(model_router, ModelRouter)
